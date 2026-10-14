"""Download the public P&ID datasets: PID2Graph (Zenodo) and Dataset-P&ID (Google Drive).

Spec: specs/2026-10-14-pid-datasets/spec.md

    python -m src.datasets.pid [--only pid2graph|dataset-pid] [--refresh-listing]

PID2Graph is one 9.3 GB zip. It is downloaded to `<name>.part` and resumed with an HTTP Range
request after an interruption. It gets its final name only after the size and MD5 from the
Zenodo API match. Only `PID2Graph/Complete/` is extracted (owner decision); the zip is kept.

Dataset-P&ID is a public Drive folder: 500 subfolders with 7 `.npy` annotation files each, and
two `.tar.gz` archives. The folder pages are parsed for file IDs, the listing is cached in
`drive_listing.json`, and anything missing or extra is reported in the manifest.

Archives are untrusted input: zip member paths are checked before extracting anything (no
"zip slip"), and tar files use Python's safe `filter="data"`.
"""

import argparse
import hashlib
import html
import json
import logging
import re
import shutil
import tarfile
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import requests
from requests.exceptions import ChunkedEncodingError
from tqdm import tqdm

from src.common import config
from src.common.http import PoliteClient

log = logging.getLogger(__name__)

OUT_DIR = config.RAW_DIR / "pid"

# PID2Graph (Zenodo). Citation copied from the Zenodo record (2026-10-14).
ZENODO_RECORD = "https://zenodo.org/records/14803338"
ZENODO_API = "https://zenodo.org/api/records/14803338"
PID2GRAPH_ZIP = "PID2Graph.zip"
PID2GRAPH_PREFIX = "PID2Graph/Complete/"
PID2GRAPH_CITATION = (
    "Stürmer, J. M., Graumann, M., & Koch, T. (2025). From Engineering Diagrams to Graphs: "
    "Digitizing P&IDs with Transformers. 2025 IEEE 12th International Conference on Data "
    "Science and Advanced Analytics (DSAA). https://doi.org/10.1109/DSAA65442.2025.11248012"
)

# Dataset-P&ID (Google Drive folder linked in the Digitize-PID paper, arXiv 2109.03794)
DRIVE_ROOT_ID = "1gMm_YKBZtXB3qUKUpI-LF1HE_MgzwfeR"
DRIVE_VIEW = "https://drive.google.com/embeddedfolderview?id={}"
DRIVE_FILE = "https://drive.usercontent.google.com/download?id={}&export=download&confirm=t"
DRIVE_ARCHIVES = ("image_2.tar.gz", "mask.tar.gz")
NPY_KINDS = ("KeyValue", "lines", "lines2", "linker", "symbols", "Table", "words")
N_DRAWINGS = 500
DATASET_PID_CITATION = (
    "Paliwal, S., Jain, A., Sharma, M., & Vig, L. (2021). Digitize-PID: Automatic Digitization "
    "of Piping and Instrumentation Diagrams. arXiv:2109.03794. "
    "https://doi.org/10.1007/978-3-030-75015-2_17"
)
DATASET_PID_LICENSE = (
    "No license file in the Drive folder; the paper says 'publicly available'. "
    "The PID2Graph Zenodo record lists 'Dataset PID' as CC BY-SA 4.0."
)

_CHUNK = 1024 * 1024


class DownloadError(Exception):
    """A download failed or its result did not match what the source promised."""


class UnsafeArchiveError(Exception):
    """An archive member would be written outside the target folder."""


@dataclass(frozen=True)
class DriveEntry:
    name: str
    id: str
    is_folder: bool


@dataclass(frozen=True)
class RemoteFile:
    url: str
    size: int
    md5: str


@dataclass
class DownloadResult:
    status: str  # "downloaded" or "skipped"
    bytes: int
    sha256: str | None = None  # None when skipped: the caller reuses or computes it
    md5: str | None = None


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def file_hashes(path: Path) -> tuple[str, str]:
    """SHA-256 and MD5 of a file, in one pass."""
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            sha.update(chunk)
            md5.update(chunk)
    return sha.hexdigest(), md5.hexdigest()


# --- Sources ---------------------------------------------------------------------------------

_ENTRY_RE = re.compile(
    r'<div class="flip-entry" id="entry-(?P<id>[\w-]+)".*?'
    r'<a href="(?P<href>[^"]+)".*?'
    r'<div class="flip-entry-title">(?P<name>[^<]*)</div>',
    re.S,
)


def parse_drive_folder(page: str) -> list[DriveEntry]:
    """Entries of a Drive `embeddedfolderview` page. A page with no entries (for example a
    sign-in page) gives an empty list, which the caller reports as missing files."""
    return [
        DriveEntry(
            name=html.unescape(m["name"]),
            id=m["id"],
            is_folder="/drive/folders/" in m["href"],
        )
        for m in _ENTRY_RE.finditer(page)
    ]


def zenodo_file(payload: dict, key: str) -> RemoteFile:
    for f in payload.get("files", []):
        if f.get("key") == key:
            algo, _, digest = f["checksum"].partition(":")
            if algo != "md5":
                raise DownloadError(f"{key}: unexpected checksum type {algo!r}")
            return RemoteFile(url=f["links"]["self"], size=int(f["size"]), md5=digest)
    raise DownloadError(f"{key} is not in the Zenodo record")


# --- Download --------------------------------------------------------------------------------


def download(
    client: PoliteClient,
    url: str,
    dest: Path,
    *,
    size: int | None = None,
    md5: str | None = None,
    force: bool = False,
    attempts: int = 10,
) -> DownloadResult:
    """Download `url` to `dest`, resumable. A file with the final name is always complete:
    data goes to `<dest>.part` and is renamed only after the size and MD5 (when known) match.
    An existing `dest` of the right size is skipped (it was verified before its rename).

    A connection that breaks mid-file (Zenodo dropped one after 283 MB on 2026-10-14) is
    retried up to `attempts` times, each time continuing from the `.part` file. After the last
    attempt the error is raised and the `.part` file is kept for the next run."""
    if not force and dest.is_file() and (size is None or dest.stat().st_size == size):
        return DownloadResult("skipped", dest.stat().st_size)

    for attempt in range(1, attempts + 1):
        try:
            return _download_once(client, url, dest, size=size, md5=md5)
        except (requests.ConnectionError, requests.Timeout, ChunkedEncodingError) as exc:
            if attempt == attempts:
                raise
            log.warning("%s: %s; resuming (attempt %d/%d)", dest.name, exc, attempt + 1, attempts)
    raise AssertionError("unreachable")


def _download_once(
    client: PoliteClient, url: str, dest: Path, *, size: int | None, md5: str | None
) -> DownloadResult:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    offset = part.stat().st_size if part.is_file() else 0
    if size is not None and offset > size:
        offset = 0  # longer than the real file: start over

    headers = {"Range": f"bytes={offset}-"} if offset else {}
    response = client.get(url, headers=headers, stream=True)
    try:
        status = response.status_code
        if status == 416 and offset and offset == size:
            pass  # the part file is already complete; only the rename was missing
        elif status not in (200, 206):
            raise DownloadError(f"{url}: HTTP {status}")
        else:
            content_type = response.headers.get("Content-Type", "")
            if content_type.startswith("text/html") and dest.suffix != ".html":
                raise DownloadError(f"{url}: got an HTML page instead of the file")
            if status == 206:
                expected = f"bytes {offset}-"
                if not response.headers.get("Content-Range", "").startswith(expected):
                    raise DownloadError(f"{url}: unexpected Content-Range")
            else:
                offset = 0  # 200: the server sent the whole file
            mode = "ab" if offset else "wb"
            total = size if size is not None else None
            with (
                part.open(mode) as f,
                tqdm(
                    total=total,
                    initial=offset,
                    unit="B",
                    unit_scale=True,
                    desc=dest.name,
                    leave=False,
                    disable=total is None or total < 50 * _CHUNK,
                ) as bar,
            ):
                if offset == 0:
                    f.truncate(0)
                for chunk in response.iter_content(chunk_size=_CHUNK):
                    f.write(chunk)
                    bar.update(len(chunk))
    finally:
        response.close()

    got = part.stat().st_size
    if size is not None and got != size:
        part.unlink()
        raise DownloadError(f"{dest.name}: size {got} bytes, expected {size}")
    sha, got_md5 = file_hashes(part)
    if md5 is not None and got_md5 != md5:
        part.unlink()
        raise DownloadError(f"{dest.name}: MD5 {got_md5}, expected {md5}")
    part.replace(dest)
    return DownloadResult("downloaded", got, sha, got_md5)


# --- Safe extraction -------------------------------------------------------------------------


def _check_member(name: str) -> None:
    path = PurePosixPath(name)
    if "\\" in name or path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", name):
        raise UnsafeArchiveError(f"unsafe path in archive: {name!r}")


def extract_zip(zip_path: Path, out_dir: Path, prefix: str) -> int:
    """Extract the members under `prefix`. All their paths are checked first, so an unsafe
    archive writes nothing. Files already extracted with the right size are skipped.
    Returns the number of files written."""
    with zipfile.ZipFile(zip_path) as z:
        members = [i for i in z.infolist() if i.filename.startswith(prefix)]
        for info in members:
            _check_member(info.filename)
        written = 0
        for info in tqdm(members, desc=f"extract {prefix}", unit="file", leave=False):
            target = out_dir / info.filename
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.is_file() and target.stat().st_size == info.file_size:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".part")
            with z.open(info) as src, tmp.open("wb") as dst:
                shutil.copyfileobj(src, dst, _CHUNK)
            tmp.replace(target)
            written += 1
    return written


def extract_tar(tar_path: Path, out_dir: Path) -> Path:
    """Extract `<name>.tar.gz` into `out_dir/<name>/` with the safe `data` filter. It goes to
    `<name>.part/` first and is renamed when complete, so the final folder is never partial.
    An existing final folder is kept as it is."""
    name = tar_path.name.removesuffix(".gz").removesuffix(".tar")
    target = out_dir / name
    if target.is_dir():
        return target
    tmp = out_dir / f"{name}.part"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    try:
        with tarfile.open(tar_path) as tar:
            tar.extractall(tmp, filter="data")
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    tmp.replace(target)
    return target


def count_by_folder(root: Path) -> dict[str, dict[str, int]]:
    """Files per subfolder of `root`, by extension, e.g. {"PID2Graph OPEN100": {".png": 12}}."""
    counts: dict[str, Counter] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            folder = path.relative_to(root).parts[0]
            counts.setdefault(folder, Counter())[path.suffix.lower()] += 1
    return {folder: dict(sorted(c.items())) for folder, c in counts.items()}


# --- PID2Graph -------------------------------------------------------------------------------


def run_pid2graph(client: PoliteClient, out_dir: Path, *, force: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    previous = _read_json(manifest_path).get("file", {})

    response = client.get(ZENODO_API)
    if response.status_code != 200:
        raise DownloadError(f"{ZENODO_API}: HTTP {response.status_code}")
    payload = response.json()
    remote = zenodo_file(payload, PID2GRAPH_ZIP)
    zip_path = out_dir / PID2GRAPH_ZIP

    log.info("PID2Graph: %s (%.2f GB)", remote.url, remote.size / 1e9)
    result = download(client, remote.url, zip_path, size=remote.size, md5=remote.md5, force=force)
    file_entry = {
        "name": PID2GRAPH_ZIP,
        "url": remote.url,
        "bytes": result.bytes,
        "md5": result.md5,
        "sha256": result.sha256,
        "status": result.status,
        "downloaded_at": _now() if result.status == "downloaded" else None,
    }
    if result.status == "skipped":
        if previous.get("bytes") == result.bytes and previous.get("sha256"):
            file_entry.update(
                md5=previous["md5"],
                sha256=previous["sha256"],
                downloaded_at=previous.get("downloaded_at"),
            )
        else:
            file_entry["sha256"], file_entry["md5"] = file_hashes(zip_path)
        if file_entry["md5"] != remote.md5:
            raise DownloadError(f"{zip_path}: MD5 {file_entry['md5']}, expected {remote.md5}")

    written = extract_zip(zip_path, out_dir, PID2GRAPH_PREFIX)
    manifest = {
        "dataset": "PID2Graph",
        "source": ZENODO_RECORD,
        "doi": payload.get("doi"),
        "published": payload.get("metadata", {}).get("publication_date"),
        "license": payload.get("metadata", {}).get("license", {}).get("id"),
        "citation": PID2GRAPH_CITATION,
        "file": file_entry,
        "extracted": {"prefix": PID2GRAPH_PREFIX, "files_written_this_run": written},
        "counts": count_by_folder(out_dir / PID2GRAPH_PREFIX),
        "checked_at": _now(),
    }
    _write_json(manifest_path, manifest)
    return manifest


# --- Dataset-P&ID ----------------------------------------------------------------------------


def _drive_page(client: PoliteClient, folder_id: str) -> list[DriveEntry]:
    response = client.get(DRIVE_VIEW.format(folder_id))
    if response.status_code != 200:
        raise DownloadError(f"Drive folder {folder_id}: HTTP {response.status_code}")
    return parse_drive_folder(response.text)


def list_drive(client: PoliteClient, root_id: str = DRIVE_ROOT_ID) -> dict:
    """{"archives": {name: id}, "folders": {folder name: {file name: id}}}"""
    listing: dict = {"archives": {}, "folders": {}, "other": {}}
    entries = _drive_page(client, root_id)
    for entry in tqdm(entries, desc="Drive listing", unit="folder"):
        if entry.is_folder:
            files = _drive_page(client, entry.id)
            listing["folders"][entry.name] = {f.name: f.id for f in files if not f.is_folder}
        elif entry.name in DRIVE_ARCHIVES:
            listing["archives"][entry.name] = entry.id
        else:
            listing["other"][entry.name] = entry.id
    return listing


def check_listing(listing: dict, n_drawings: int = N_DRAWINGS) -> dict[str, list[str]]:
    """Compare a Drive listing with what the paper and folder promise: `n_drawings` folders
    named 0..n-1 with 7 `.npy` files each, plus the archives."""
    missing, extra = [], []
    folders = listing.get("folders", {})
    for i in range(n_drawings):
        name = str(i)
        if name not in folders:
            missing.append(f"{name}/")
            continue
        expected = {f"{i}_{kind}.npy" for kind in NPY_KINDS}
        missing += [f"{name}/{f}" for f in sorted(expected - set(folders[name]))]
        extra += [f"{name}/{f}" for f in sorted(set(folders[name]) - expected)]
    expected_names = {str(i) for i in range(n_drawings)}
    extra += [f"{name}/" for name in sorted(set(folders) - expected_names)]
    missing += [a for a in DRIVE_ARCHIVES if a not in listing.get("archives", {})]
    extra += sorted(listing.get("other", {}))
    return {"missing": missing, "extra": extra}


def run_dataset_pid(
    client: PoliteClient,
    out_dir: Path,
    *,
    n_drawings: int = N_DRAWINGS,
    refresh_listing: bool = False,
    force: bool = False,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    listing_path = out_dir / "drive_listing.json"
    manifest_path = out_dir / "manifest.json"
    previous = {f["path"]: f for f in _read_json(manifest_path).get("files", [])}

    if listing_path.is_file() and not refresh_listing:
        listing = _read_json(listing_path)
    else:
        listing = list_drive(client)
        listing["listed_at"] = _now()
        _write_json(listing_path, listing)

    jobs = [(name, file_id) for name, file_id in listing["archives"].items()]
    for folder, files in sorted(listing["folders"].items(), key=lambda kv: int(kv[0])):
        if folder.isdigit() and int(folder) < n_drawings:
            jobs += [(f"{folder}/{name}", file_id) for name, file_id in sorted(files.items())]

    entries, errors = [], []
    for rel, file_id in tqdm(jobs, desc="Dataset-P&ID", unit="file"):
        path = out_dir / rel
        _check_member(rel)
        try:
            result = download(client, DRIVE_FILE.format(file_id), path, force=force)
        except (DownloadError, requests.RequestException, OSError) as exc:
            errors.append({"path": rel, "error": f"{type(exc).__name__}: {exc}"})
            continue
        entry = {
            "path": rel,
            "drive_id": file_id,
            "bytes": result.bytes,
            "sha256": result.sha256,
            "downloaded_at": _now() if result.status == "downloaded" else None,
        }
        if result.status == "skipped":
            old = previous.get(rel, {})
            if old.get("bytes") == result.bytes and old.get("sha256"):
                entry.update(sha256=old["sha256"], downloaded_at=old.get("downloaded_at"))
            else:
                entry["sha256"] = file_hashes(path)[0]
        entries.append(entry)

    extracted = []
    for archive in DRIVE_ARCHIVES:
        if (out_dir / archive).is_file():
            extracted.append(extract_tar(out_dir / archive, out_dir).name)

    gaps = check_listing(listing, n_drawings)
    manifest = {
        "dataset": "Dataset-P&ID",
        "source": f"https://drive.google.com/drive/folders/{DRIVE_ROOT_ID}",
        "paper": "https://arxiv.org/abs/2109.03794",
        "license": DATASET_PID_LICENSE,
        "citation": DATASET_PID_CITATION,
        "listed_at": listing.get("listed_at"),
        "files": entries,
        "errors": errors,
        "missing": gaps["missing"],
        "extra": gaps["extra"],
        "extracted": extracted,
        "checked_at": _now(),
    }
    _write_json(manifest_path, manifest)
    return manifest


# --- CLI -------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download PID2Graph and Dataset-P&ID.")
    parser.add_argument("--only", choices=["pid2graph", "dataset-pid"], default=None)
    parser.add_argument("--refresh-listing", action="store_true", help="re-read the Drive folder")
    parser.add_argument("--force", action="store_true", help="download existing files again")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    client = PoliteClient(timeout=120.0)

    if args.only in (None, "pid2graph"):
        m = run_pid2graph(client, args.out / "pid2graph", force=args.force)
        print(f"PID2Graph: {m['file']['status']}, {m['file']['bytes']:,} bytes, MD5 OK")
        for folder, counts in m["counts"].items():
            print(f"  {folder}: {counts}")
    if args.only in (None, "dataset-pid"):
        m = run_dataset_pid(
            client, args.out / "dataset_pid", refresh_listing=args.refresh_listing, force=args.force
        )
        print(f"Dataset-P&ID: {len(m['files'])} files, extracted {m['extracted']}")
        print(f"  missing ({len(m['missing'])}): {m['missing'][:20]}")
        print(f"  extra ({len(m['extra'])}): {m['extra'][:20]}")
        print(f"  errors ({len(m['errors'])}): {m['errors'][:5]}")


if __name__ == "__main__":
    main()
