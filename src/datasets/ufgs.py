"""Download UFGS (Unified Facilities Guide Specifications) PDFs from WBDG.

Spec: specs/2026-10-07-ufgs-download/spec.md

    python -m src.datasets.ufgs --divisions 01 03 05 22 23 26 33 [--limit N] [--dry-run] [--force]

The section list comes from the WBDG sitemap. Each PDF URL is built from the section number
(e.g. 32-13-15-20 -> "UFGS 32 13 15.20.pdf"). Sections whose PDF isn't at that URL (WBDG's S3
answers 403) are recorded as `not_found`, never guessed.
"""

import argparse
import hashlib
import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests
from tqdm import tqdm

from src.common import config
from src.common.http import PoliteClient

log = logging.getLogger(__name__)

SITEMAP_URL = "https://www.wbdg.org/api/sitemap/documents.xml"
PDF_BASE_URL = "https://www.wbdg.org/FFC/DOD/UFGS/"
DEFAULT_DIVISIONS = ("01", "03", "05", "22", "23", "26", "33")
OUT_DIR = config.RAW_DIR / "ufgs"
STATUSES = ("downloaded", "skipped", "not_found", "error")

_SECTION_PAGE = re.compile(r"/dod/ufgs/ufgs-(\d{2}(?:-\d{2})+)$")
_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_CHUNK = 64 * 1024


def pdf_name(section_id: str) -> str:
    """'03-30-00' -> 'UFGS 03 30 00'; '32-13-15-20' -> 'UFGS 32 13 15.20';
    '01-45-00-15-10' -> 'UFGS 01 45 00.15 10'."""
    parts = section_id.split("-")
    name = " ".join(parts[:3])
    if len(parts) > 3:
        name += "." + parts[3]
    if len(parts) > 4:
        name += " " + " ".join(parts[4:])
    return f"UFGS {name}"


@dataclass(frozen=True)
class Section:
    section_id: str  # e.g. "03-30-00"
    page_url: str

    @property
    def division(self) -> str:
        return self.section_id[:2]

    @property
    def pdf_url(self) -> str:
        return PDF_BASE_URL + quote(pdf_name(self.section_id) + ".pdf")


def parse_sitemap(xml_text: str) -> list[Section]:
    """Current UFGS sections in the sitemap, unique and sorted. Archive, division and
    non-UFGS pages are ignored."""
    root = ET.fromstring(xml_text)
    sections = {}
    for loc in root.iter(f"{_SITEMAP_NS}loc"):
        url = (loc.text or "").strip()
        match = _SECTION_PAGE.search(url)
        if match:
            sections[match.group(1)] = Section(match.group(1), url)
    return [sections[key] for key in sorted(sections)]


def filter_divisions(sections: list[Section], divisions) -> list[Section]:
    wanted = set(divisions)
    return [s for s in sections if s.division in wanted]


def local_path(out_dir: Path, section: Section) -> Path:
    return out_dir / section.division / f"UFGS_{section.section_id.replace('-', '_')}.pdf"


def _is_pdf(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("rb") as f:
        return f.read(4) == b"%PDF"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def download_section(
    client: PoliteClient, section: Section, out_dir: Path, *, force: bool = False
) -> dict:
    """Download one section PDF and return its manifest entry."""
    path = local_path(out_dir, section)
    entry = {
        "section_id": section.section_id,
        "division": section.division,
        "page_url": section.page_url,
        "pdf_url": section.pdf_url,
        "local_path": path.relative_to(out_dir).as_posix(),
        "status": None,
        "http_status": None,
        "bytes": None,
        "sha256": None,
        "downloaded_at": None,
        "error": None,
    }

    if not force and _is_pdf(path):
        entry.update(status="skipped", bytes=path.stat().st_size, sha256=_sha256(path))
        return entry

    part = path.with_name(path.name + ".part")
    try:
        response = client.get(section.pdf_url, stream=True)
        entry["http_status"] = response.status_code
        if response.status_code in (403, 404):
            entry["status"] = "not_found"
            return entry
        if response.status_code != 200:
            entry.update(status="error", error=f"HTTP {response.status_code}")
            return entry

        path.parent.mkdir(parents=True, exist_ok=True)
        digest, size, head = hashlib.sha256(), 0, b""
        with part.open("wb") as f:
            for chunk in response.iter_content(chunk_size=_CHUNK):
                if len(head) < 4:
                    head += chunk[: 4 - len(head)]
                digest.update(chunk)
                size += len(chunk)
                f.write(chunk)
        response.close()

        if head != b"%PDF":
            part.unlink()
            entry.update(status="error", error=f"Not a PDF (starts with {head!r})")
            return entry

        part.replace(path)  # atomic: the final name only ever holds a complete file
        entry.update(
            status="downloaded", bytes=size, sha256=digest.hexdigest(), downloaded_at=_now()
        )
    except (requests.RequestException, OSError) as exc:
        part.unlink(missing_ok=True)
        entry.update(status="error", error=f"{type(exc).__name__}: {exc}")
    return entry


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _previous_entries(manifest_path: Path) -> dict[str, dict]:
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {e["section_id"]: e for e in data.get("sections", [])}


def run(
    client: PoliteClient,
    divisions,
    out_dir: Path = OUT_DIR,
    *,
    limit: int | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Download all sections of `divisions`; write and return the manifest."""
    response = client.get(SITEMAP_URL)
    response.raise_for_status()
    sections = filter_divisions(parse_sitemap(response.text), divisions)[:limit]
    log.info("%d sections in divisions %s", len(sections), ", ".join(divisions))

    manifest = {
        "source": SITEMAP_URL,
        "started_at": _now(),
        "finished_at": None,
        "divisions": list(divisions),
        "counts": dict.fromkeys(STATUSES, 0),
        "sections": [],
    }
    if dry_run:
        manifest["sections"] = [
            {"section_id": s.section_id, "pdf_url": s.pdf_url} for s in sections
        ]
        return manifest

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    previous = _previous_entries(manifest_path)

    for section in tqdm(sections, desc="UFGS", unit="pdf"):
        entry = download_section(client, section, out_dir, force=force)
        if entry["status"] == "skipped":
            entry["downloaded_at"] = previous.get(section.section_id, {}).get("downloaded_at")
        manifest["sections"].append(entry)
        manifest["counts"][entry["status"]] += 1
        _write_json(manifest_path, manifest)  # after every section: progress survives a crash

    manifest["finished_at"] = _now()
    _write_json(manifest_path, manifest)
    return manifest


def summary(manifest: dict) -> str:
    lines = [
        f"Total: {len(manifest['sections'])}  "
        + "  ".join(f"{k}={v}" for k, v in manifest["counts"].items())
    ]
    per_div: dict[str, dict[str, int]] = {}
    for e in manifest["sections"]:
        if "status" in e:
            per_div.setdefault(e["division"], dict.fromkeys(STATUSES, 0))[e["status"]] += 1
    for div, counts in sorted(per_div.items()):
        lines.append(f"  {div}: " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    size = sum(e.get("bytes") or 0 for e in manifest["sections"])
    lines.append(f"Size on disk (downloaded + skipped): {size / 1e6:.1f} MB")
    missing = [e["section_id"] for e in manifest["sections"] if e.get("status") == "not_found"]
    if missing:
        lines.append(f"not_found ({len(missing)}): " + ", ".join(missing))
    errors = [e for e in manifest["sections"] if e.get("status") == "error"]
    for e in errors:
        lines.append(f"error {e['section_id']}: {e['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download UFGS PDFs from WBDG.")
    parser.add_argument("--divisions", nargs="+", default=list(DEFAULT_DIVISIONS))
    parser.add_argument("--limit", type=int, default=None, help="only the first N sections")
    parser.add_argument("--dry-run", action="store_true", help="list sections, download nothing")
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    manifest = run(
        PoliteClient(),
        args.divisions,
        args.out,
        limit=args.limit,
        dry_run=args.dry_run,
        force=args.force,
    )
    if args.dry_run:
        for s in manifest["sections"]:
            print(s["section_id"], s["pdf_url"])
        print(f"{len(manifest['sections'])} sections (dry run, nothing downloaded)")
    else:
        print(summary(manifest))


if __name__ == "__main__":
    main()
