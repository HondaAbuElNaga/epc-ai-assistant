"""Download UFGS (Unified Facilities Guide Specifications) PDFs from WBDG.

Spec: specs/2026-10-07-ufgs-download/spec.md (v2)

    python -m src.datasets.ufgs [--divisions 01 03 ...] [--limit N] [--dry-run] [--force]
                                [--keep-retired]

The section list comes from the WBDG sitemap, which holds current *and* retired sections. For
each one we ask WBDG's (undocumented) API whether it is ACTIVE and which file is its current PDF,
then download that exact file. Retired sections are recorded, never downloaded, and a PDF left
on disk by an earlier run is deleted. Anything unexpected is an `error`, never a guess.
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

import requests
from tqdm import tqdm

from src.common import config
from src.common.http import PoliteClient

log = logging.getLogger(__name__)

SITEMAP_URL = "https://www.wbdg.org/api/sitemap/documents.xml"
API_URL = "https://www.wbdg.org/api/documents/ufgs-{}"
# Building trades + general requirements, then the process divisions (40-46) used in EPC plants
DEFAULT_DIVISIONS = (
    "01", "03", "05", "22", "23", "26", "33", "40", "41", "42", "43", "44", "46",
)  # fmt: skip
OUT_DIR = config.RAW_DIR / "ufgs"
STATUSES = ("downloaded", "skipped", "retired", "no_pdf", "not_found", "error")

_SECTION_PAGE = re.compile(r"/dod/ufgs/ufgs-(\d{2}(?:-\d{2})+)$")
_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_CHUNK = 64 * 1024


def pdf_name(section_id: str) -> str:
    """WBDG's file name, also the base of our local name.
    '03-30-00' -> 'UFGS 03 30 00'; '32-13-15-20' -> 'UFGS 32 13 15.20';
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
    def api_url(self) -> str:
        return API_URL.format(self.section_id)


def parse_sitemap(xml_text: str) -> list[Section]:
    """UFGS sections in the sitemap (current and retired), unique and sorted. Archive,
    division and non-UFGS pages are ignored."""
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


def parse_api(payload: dict) -> dict:
    """Read an API answer. Returns title, api_status, publish_date, pdf_url, error and
    `status`: None when there is exactly one current PDF to download, else the final status."""
    info = {
        "title": None,
        "api_status": None,
        "publish_date": None,
        "pdf_url": None,
        "status": None,
        "error": None,
    }
    if payload.get("success") is False:
        info["status"] = "not_found"
        return info
    data = payload.get("data")
    if not isinstance(data, dict) or "status" not in data or "mediaFiles" not in data:
        info.update(status="error", error="Unexpected API answer: no data.status/mediaFiles")
        return info

    info.update(
        title=data.get("title"), api_status=data["status"], publish_date=data.get("publishDate")
    )
    if data["status"] != "ACTIVE":
        info["status"] = "retired"
        return info

    # Older versions stay in mediaFiles (isArchived); the .zip holds the editable source
    current = [
        m
        for m in data["mediaFiles"]
        if m.get("isCurrent")
        and not m.get("isArchived")
        and str(m.get("fileName", "")).lower().endswith(".pdf")
    ]
    if not current:
        info["status"] = "no_pdf"
    elif len(current) > 1:
        info.update(status="error", error=f"{len(current)} current PDFs in the API answer")
    else:
        info["pdf_url"] = current[0]["fileUrl"]
    return info


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
    """Ask the API about one section, download its current PDF if it is ACTIVE, and return
    its manifest entry."""
    path = local_path(out_dir, section)
    entry = {
        "section_id": section.section_id,
        "division": section.division,
        "page_url": section.page_url,
        "api_url": section.api_url,
        "title": None,
        "api_status": None,
        "publish_date": None,
        "pdf_url": None,
        "local_path": path.relative_to(out_dir).as_posix(),
        "status": None,
        "http_status": None,
        "bytes": None,
        "sha256": None,
        "downloaded_at": None,
        "error": None,
        "removed": False,
    }

    part = path.with_name(path.name + ".part")
    try:
        response = client.get(section.api_url)
        entry["http_status"] = response.status_code
        if response.status_code == 404:
            entry["status"] = "not_found"
            return entry
        if response.status_code != 200:
            entry.update(status="error", error=f"API HTTP {response.status_code}")
            return entry
        try:
            payload = response.json()
        except ValueError:
            entry.update(status="error", error="API answer is not JSON")
            return entry
        entry.update(parse_api(payload))
        if entry["status"] is not None:
            return entry

        if not force and _is_pdf(path):
            entry.update(status="skipped", bytes=path.stat().st_size, sha256=_sha256(path))
            return entry

        # The API promised this file, so any non-200 here is an error, not "not found"
        response = client.get(entry["pdf_url"], stream=True)
        entry["http_status"] = response.status_code
        if response.status_code != 200:
            entry.update(status="error", error=f"PDF HTTP {response.status_code}")
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


def remove_retired(out_dir: Path, manifest: dict) -> int:
    """Delete our own PDF of every section marked `retired` (that exact file, nothing else)."""
    removed = 0
    for entry in manifest["sections"]:
        if entry.get("status") != "retired":
            continue
        path = out_dir / entry["local_path"]
        if path.is_file():
            path.unlink()
            entry["removed"] = True
            removed += 1
            log.info("Removed retired %s (%s)", entry["section_id"], entry["local_path"])
    return removed


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
    keep_retired: bool = False,
) -> dict:
    """Check and download all sections of `divisions`; write and return the manifest."""
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
        "removed": 0,
        "sections": [],
    }
    if dry_run:
        manifest["sections"] = [
            {"section_id": s.section_id, "api_url": s.api_url} for s in sections
        ]
        return manifest

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    previous = _previous_entries(manifest_path)

    for section in tqdm(sections, desc="UFGS", unit="section"):
        entry = download_section(client, section, out_dir, force=force)
        if entry["status"] == "skipped":
            entry["downloaded_at"] = previous.get(section.section_id, {}).get("downloaded_at")
        manifest["sections"].append(entry)
        manifest["counts"][entry["status"]] += 1
        _write_json(manifest_path, manifest)  # after every section: progress survives a crash

    if not keep_retired:
        manifest["removed"] = remove_retired(out_dir, manifest)
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
    lines.append(f"Retired PDFs removed from disk: {manifest.get('removed', 0)}")
    for status in ("no_pdf", "not_found"):
        ids = [e["section_id"] for e in manifest["sections"] if e.get("status") == status]
        if ids:
            lines.append(f"{status} ({len(ids)}): " + ", ".join(ids))
    for e in manifest["sections"]:
        if e.get("status") == "error":
            lines.append(f"error {e['section_id']}: {e['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download active UFGS PDFs from WBDG.")
    parser.add_argument("--divisions", nargs="+", default=list(DEFAULT_DIVISIONS))
    parser.add_argument("--limit", type=int, default=None, help="only the first N sections")
    parser.add_argument("--dry-run", action="store_true", help="list sections, download nothing")
    parser.add_argument("--force", action="store_true", help="re-download existing files")
    parser.add_argument(
        "--keep-retired", action="store_true", help="don't delete PDFs of retired sections"
    )
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
        keep_retired=args.keep_retired,
    )
    if args.dry_run:
        for s in manifest["sections"]:
            print(s["section_id"], s["api_url"])
        print(f"{len(manifest['sections'])} sections (dry run, nothing downloaded)")
    else:
        print(summary(manifest))


if __name__ == "__main__":
    main()
