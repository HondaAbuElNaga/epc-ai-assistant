"""SHA-256 checksums of every file under data/raw/, stored in data/checksums.json.

Spec: specs/2026-10-16-data-catalog/spec.md

    python -m src.datasets.checksums --write  [--dataset NAME]
    python -m src.datasets.checksums --verify [--dataset NAME] [--quick]

`--write` hashes the files and saves sizes + hashes. `--verify` compares the disk against the
saved file and reports missing, changed and new files (exit code 1 if any is missing or
changed). `--quick` compares sizes only, which takes seconds instead of minutes.

Download records (manifest.json, ...) and unfinished downloads (*.part) are skipped: they change
on every re-run of a download script, while the data itself must not change.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from tqdm import tqdm

from src.common import config

RAW_DIR = config.RAW_DIR
OUT_FILE = config.DATA_DIR / "checksums.json"

# Dataset name -> folder under data/raw/. Files elsewhere count as "other".
DATASETS = {
    "ufgs": "ufgs",
    "ghent": "project_controls/ghent",
    "pid2graph": "pid/pid2graph",
    "dataset_pid": "pid/dataset_pid",
}
SKIP_NAMES = {".gitkeep", "manifest.json", "download.json", "drive_listing.json"}
SKIP_SUFFIXES = {".part"}
CHUNK = 1024 * 1024  # 1 MiB: big files are never read into memory at once


@dataclass
class Report:
    """Result of `verify`: `passed` is False if any file is missing or changed."""

    ok: int = 0
    missing: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.missing and not self.changed


def dataset_of(key: str) -> str:
    """Dataset name for a path key like 'pid/pid2graph/PID2Graph.zip'."""
    for name, folder in DATASETS.items():
        if key.startswith(folder + "/"):
            return name
    return "other"


def sha256_file(path: Path, chunk_size: int = CHUNK) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _in_scope(key: str, dataset: str | None) -> bool:
    return dataset is None or dataset_of(key) == dataset


def _data_files(root: Path, dataset: str | None = None) -> dict[str, Path]:
    """Path key (relative to root, '/' separators) -> path, for every data file in scope."""
    files = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
            continue
        key = path.relative_to(root).as_posix()
        if _in_scope(key, dataset):
            files[key] = path
    return dict(sorted(files.items()))


def _progress(total_bytes: int, desc: str) -> tqdm:
    return tqdm(total=total_bytes, unit="B", unit_scale=True, desc=desc, disable=None)


def scan(root: Path, dataset: str | None = None) -> dict[str, dict]:
    """Size and SHA-256 of every data file under `root` (or one dataset of it)."""
    files = _data_files(root, dataset)
    sizes = {key: path.stat().st_size for key, path in files.items()}
    entries = {}
    with _progress(sum(sizes.values()), "hashing") as bar:
        for key, path in files.items():
            entries[key] = {"bytes": sizes[key], "sha256": sha256_file(path)}
            bar.update(sizes[key])
    return entries


def _totals(entries: dict[str, dict]) -> dict[str, dict]:
    totals: dict[str, dict] = {}
    for key, entry in entries.items():
        t = totals.setdefault(dataset_of(key), {"files": 0, "bytes": 0})
        t["files"] += 1
        t["bytes"] += entry["bytes"]
    return dict(sorted(totals.items()))


def _load(out: Path) -> dict:
    if not out.is_file():
        raise FileNotFoundError(f"{out} not found: run with --write first")
    return json.loads(out.read_text(encoding="utf-8"))


def write(root: Path = RAW_DIR, out: Path = OUT_FILE, dataset: str | None = None) -> dict:
    """Hash the files and save them to `out`. With `dataset`, only that dataset's entries are
    replaced. The file is left untouched when nothing changed, so `git diff` stays clean."""
    old = _load(out) if out.is_file() else {"files": {}}
    entries = {k: v for k, v in old["files"].items() if not _in_scope(k, dataset)}
    entries.update(scan(root, dataset))
    entries = dict(sorted(entries.items()))
    if entries == old["files"]:
        return old
    doc = {
        "algorithm": "sha256",
        "root": "data/raw",
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "datasets": _totals(entries),
        "files": entries,
    }
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc


def verify(
    root: Path = RAW_DIR, out: Path = OUT_FILE, dataset: str | None = None, quick: bool = False
) -> Report:
    """Compare the files on disk with `out`. `quick` compares sizes only."""
    recorded = {k: v for k, v in _load(out)["files"].items() if _in_scope(k, dataset)}
    on_disk = _data_files(root, dataset)
    report = Report(new=[k for k in on_disk if k not in recorded])

    present = {k: on_disk[k] for k in recorded if k in on_disk}
    report.missing = [k for k in recorded if k not in on_disk]
    sizes = {k: p.stat().st_size for k, p in present.items()}
    with _progress(0 if quick else sum(sizes.values()), "verifying") as bar:
        for key, path in present.items():
            entry = recorded[key]
            same = sizes[key] == entry["bytes"]
            if same and not quick:
                same = sha256_file(path) == entry["sha256"]
                bar.update(sizes[key])
            if same:
                report.ok += 1
            else:
                report.changed.append(key)
    return report


def _print_list(label: str, keys: list[str], limit: int = 20) -> None:
    print(f"{label} ({len(keys)})" + (":" if keys else ""))
    for key in keys[:limit]:
        print(f"  {key}")
    if len(keys) > limit:
        print(f"  ... and {len(keys) - limit} more")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or verify checksums of data/raw/.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="hash the files and save them")
    mode.add_argument("--verify", action="store_true", help="check the files against the saved")
    parser.add_argument("--quick", action="store_true", help="verify sizes only (fast)")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default=None)
    parser.add_argument("--root", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUT_FILE)
    args = parser.parse_args(argv)
    if args.quick and args.write:
        parser.error("--quick only works with --verify")

    if args.write:
        doc = write(args.root, args.out, args.dataset)
        for name, t in doc["datasets"].items():
            print(f"{name}: {t['files']:,} files, {t['bytes']:,} bytes")
        print(f"saved {len(doc['files']):,} entries to {args.out}")
        return 0

    report = verify(args.root, args.out, args.dataset, args.quick)
    print(f"ok: {report.ok:,}" + (" (sizes only)" if args.quick else ""))
    _print_list("missing", report.missing)
    _print_list("changed", report.changed)
    _print_list("new, not in the checksum file (warning)", report.new)
    print("PASSED" if report.passed else "FAILED")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
