"""UFGS downloader. Spec: specs/2026-10-07-ufgs-download/spec.md.

Unit tests use a fake HTTP session (no network). The `network` test hits WBDG for one PDF.
"""

import hashlib
import json
from pathlib import Path

import pytest
import requests

from src.common.http import PoliteClient
from src.datasets import ufgs

FIXTURES = Path(__file__).parent / "fixtures"
SITEMAP = (FIXTURES / "ufgs_sitemap_sample.xml").read_text(encoding="utf-8")
PDF_BYTES = b"%PDF-1.4\n% tiny test pdf\n%%EOF\n"


class FakeResponse:
    def __init__(self, status_code=200, body=b"", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = body.decode("utf-8", errors="replace")

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def close(self):
        pass


class FakeSession:
    """Returns queued responses per URL (the last one repeats) and records every call."""

    def __init__(self, routes):
        self.routes = {url: list(resps) for url, resps in routes.items()}
        self.calls = []
        self.headers = {}

    def get(self, url, **kwargs):
        self.calls.append(url)
        queue = self.routes.get(url)
        if not queue:
            return FakeResponse(404)
        if isinstance(queue[0], Exception):
            raise queue.pop(0)
        return queue.pop(0) if len(queue) > 1 else queue[0]


def make_client(routes):
    session = FakeSession(routes)
    sleeps = []
    client = PoliteClient(session=session, delay=1.0, backoff=0.5, sleep=sleeps.append)
    return client, session, sleeps


def section(section_id):
    return ufgs.Section(section_id, f"https://www.wbdg.org/dod/ufgs/ufgs-{section_id}")


# --- section list -------------------------------------------------------------------------


def test_parse_sitemap_keeps_current_sections_only_sorted_and_unique():
    ids = [s.section_id for s in ufgs.parse_sitemap(SITEMAP)]
    assert ids == ["01-33-00", "01-45-00-15-10", "03-30-00", "32-13-15-20", "33-32-13-13"]


def test_filter_divisions():
    sections = ufgs.parse_sitemap(SITEMAP)
    kept = ufgs.filter_divisions(sections, ["01", "33"])
    assert [s.section_id for s in kept] == ["01-33-00", "01-45-00-15-10", "33-32-13-13"]


@pytest.mark.parametrize(
    ("section_id", "name"),
    [
        ("03-30-00", "UFGS 03 30 00"),
        ("01-33-00", "UFGS 01 33 00"),
        ("32-13-15-20", "UFGS 32 13 15.20"),
        ("01-45-00-15-10", "UFGS 01 45 00.15 10"),
    ],
)
def test_pdf_name_follows_verified_patterns(section_id, name):
    assert ufgs.pdf_name(section_id) == name


def test_pdf_url_and_local_path(tmp_path):
    s = section("01-45-00-15-10")
    assert s.pdf_url == "https://www.wbdg.org/FFC/DOD/UFGS/UFGS%2001%2045%2000.15%2010.pdf"
    assert ufgs.local_path(tmp_path, s) == tmp_path / "01" / "UFGS_01_45_00_15_10.pdf"


# --- downloading --------------------------------------------------------------------------


def test_download_writes_pdf_with_sha256(tmp_path):
    s = section("03-30-00")
    client, _, _ = make_client({s.pdf_url: [FakeResponse(200, PDF_BYTES)]})

    entry = ufgs.download_section(client, s, tmp_path)

    path = ufgs.local_path(tmp_path, s)
    assert entry["status"] == "downloaded"
    assert path.read_bytes() == PDF_BYTES
    assert entry["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert entry["bytes"] == len(PDF_BYTES)
    assert not path.with_name(path.name + ".part").exists()


def test_403_is_not_found_and_not_retried(tmp_path):
    s = section("33-32-13-13")
    client, session, _ = make_client({s.pdf_url: [FakeResponse(403)]})

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "not_found"
    assert entry["http_status"] == 403
    assert session.calls == [s.pdf_url]
    assert not ufgs.local_path(tmp_path, s).exists()


def test_503_is_retried_then_succeeds(tmp_path):
    s = section("03-30-00")
    client, session, sleeps = make_client(
        {s.pdf_url: [FakeResponse(503), FakeResponse(200, PDF_BYTES)]}
    )

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "downloaded"
    assert len(session.calls) == 2
    assert 0.5 in sleeps  # backoff before the retry


def test_connection_error_is_retried(tmp_path):
    s = section("03-30-00")
    client, session, _ = make_client(
        {s.pdf_url: [requests.ConnectionError("boom"), FakeResponse(200, PDF_BYTES)]}
    )

    assert ufgs.download_section(client, s, tmp_path)["status"] == "downloaded"
    assert len(session.calls) == 2


def test_non_pdf_body_is_rejected_and_leaves_no_file(tmp_path):
    s = section("03-30-00")
    client, _, _ = make_client({s.pdf_url: [FakeResponse(200, b"<html>error</html>")]})

    entry = ufgs.download_section(client, s, tmp_path)

    path = ufgs.local_path(tmp_path, s)
    assert entry["status"] == "error"
    assert "PDF" in entry["error"]
    assert not path.exists()
    assert not path.with_name(path.name + ".part").exists()


def test_existing_pdf_is_skipped_and_force_redownloads(tmp_path):
    s = section("03-30-00")
    path = ufgs.local_path(tmp_path, s)
    path.parent.mkdir(parents=True)
    path.write_bytes(PDF_BYTES)
    client, session, _ = make_client({s.pdf_url: [FakeResponse(200, PDF_BYTES)]})

    assert ufgs.download_section(client, s, tmp_path)["status"] == "skipped"
    assert session.calls == []

    assert ufgs.download_section(client, s, tmp_path, force=True)["status"] == "downloaded"
    assert session.calls == [s.pdf_url]


def test_delay_between_requests():
    client, _, sleeps = make_client({"https://x/a": [FakeResponse(200)]})
    client.get("https://x/a")
    client.get("https://x/a")
    client.get("https://x/a")
    assert sleeps == [1.0, 1.0]  # no wait before the first request


# --- full run -----------------------------------------------------------------------------


def _run_routes():
    ok = [FakeResponse(200, PDF_BYTES)]
    return {
        ufgs.SITEMAP_URL: [FakeResponse(200, SITEMAP.encode())],
        section("01-33-00").pdf_url: ok,
        section("01-45-00-15-10").pdf_url: ok,
        section("33-32-13-13").pdf_url: [FakeResponse(403)],
    }


def test_run_writes_manifest_with_every_section(tmp_path):
    client, _, _ = make_client(_run_routes())

    manifest = ufgs.run(client, ["01", "33"], tmp_path)

    on_disk = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest
    ids = [e["section_id"] for e in manifest["sections"]]
    assert ids == ["01-33-00", "01-45-00-15-10", "33-32-13-13"]
    assert manifest["counts"] == {"downloaded": 2, "skipped": 0, "not_found": 1, "error": 0}
    assert manifest["divisions"] == ["01", "33"]


def test_second_run_skips_everything_and_keeps_download_time(tmp_path):
    client, _, _ = make_client(_run_routes())
    first = ufgs.run(client, ["01"], tmp_path)
    client, session, _ = make_client(_run_routes())

    second = ufgs.run(client, ["01"], tmp_path)

    assert second["counts"]["skipped"] == 2
    assert session.calls == [ufgs.SITEMAP_URL]
    assert [e["downloaded_at"] for e in second["sections"]] == [
        e["downloaded_at"] for e in first["sections"]
    ]


def test_limit_and_dry_run(tmp_path):
    client, session, _ = make_client(_run_routes())

    manifest = ufgs.run(client, ["01", "33"], tmp_path, limit=1, dry_run=True)

    assert [e["section_id"] for e in manifest["sections"]] == ["01-33-00"]
    assert session.calls == [ufgs.SITEMAP_URL]
    assert not (tmp_path / "manifest.json").exists()


# --- real network -------------------------------------------------------------------------


@pytest.mark.network
def test_real_download_of_one_verified_section(tmp_path):
    entry = ufgs.download_section(PoliteClient(), section("01-33-00"), tmp_path)

    assert entry["status"] == "downloaded", entry
    assert ufgs.local_path(tmp_path, section("01-33-00")).read_bytes()[:4] == b"%PDF"
    assert len(entry["sha256"]) == 64
