"""UFGS downloader. Spec: specs/2026-10-07-ufgs-download/spec.md (v2: API-based, active only).

Unit tests use a fake HTTP session (no network). The `network` tests hit WBDG.
"""

import copy
import hashlib
import json
from pathlib import Path

import pytest
import requests

from src.common.http import PoliteClient
from src.datasets import ufgs

FIXTURES = Path(__file__).parent / "fixtures"
SITEMAP = (FIXTURES / "ufgs_sitemap_sample.xml").read_text(encoding="utf-8")
# Real API answer for 03-30-00 (trimmed to the fields we use): one current PDF + archived ones
API_ACTIVE = json.loads((FIXTURES / "ufgs_api_03-30-00.json").read_text(encoding="utf-8"))
ACTIVE_PDF_URL = "https://nibs-s3-wbdg3-production.s3.us-east-1.amazonaws.com/FFC/DOD/UFGS/UFGS%2003%2030%2000.pdf"
PDF_BYTES = b"%PDF-1.4\n% tiny test pdf\n%%EOF\n"


class FakeResponse:
    def __init__(self, status_code=200, body=b"", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)

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


def api_json(payload):
    return FakeResponse(200, json.dumps(payload).encode())


def api_payload(section_id, status="ACTIVE", pdf_urls=None):
    """A minimal API answer. `pdf_urls` become current, non-archived PDF media files."""
    media = [
        {"fileName": f"{ufgs.pdf_name(section_id)}.pdf", "fileUrl": url, "versionNumber": 4,
         "isCurrent": True, "isArchived": False}
        for url in (pdf_urls or [])
    ]  # fmt: skip
    return {
        "success": True,
        "data": {
            "title": f"{ufgs.pdf_name(section_id)} Test Title",
            "status": status,
            "publishDate": "2020-01-01T00:00:00.000Z",
            "mediaFiles": media,
        },
    }


def pdf_url_for(section_id):
    return f"https://s3.example/FFC/DOD/UFGS/{section_id}.pdf"


def active_routes(section_id, pdf_responses=None):
    s = section(section_id)
    return {
        s.api_url: [api_json(api_payload(section_id, pdf_urls=[pdf_url_for(section_id)]))],
        pdf_url_for(section_id): pdf_responses or [FakeResponse(200, PDF_BYTES)],
    }


# --- section list -------------------------------------------------------------------------


def test_parse_sitemap_keeps_current_sections_only_sorted_and_unique():
    ids = [s.section_id for s in ufgs.parse_sitemap(SITEMAP)]
    assert ids == ["01-33-00", "01-45-00-15-10", "03-30-00", "32-13-15-20", "33-32-13-13"]


def test_filter_divisions():
    sections = ufgs.parse_sitemap(SITEMAP)
    kept = ufgs.filter_divisions(sections, ["01", "33"])
    assert [s.section_id for s in kept] == ["01-33-00", "01-45-00-15-10", "33-32-13-13"]


def test_default_divisions_are_the_approved_13():
    assert ufgs.DEFAULT_DIVISIONS == (
        "01", "03", "05", "22", "23", "26", "33", "40", "41", "42", "43", "44", "46",
    )  # fmt: skip


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


def test_api_url_and_local_path(tmp_path):
    s = section("01-45-00-15-10")
    assert s.api_url == "https://www.wbdg.org/api/documents/ufgs-01-45-00-15-10"
    assert ufgs.local_path(tmp_path, s) == tmp_path / "01" / "UFGS_01_45_00_15_10.pdf"


# --- reading the API answer ---------------------------------------------------------------


def test_parse_api_real_answer_picks_the_current_pdf_not_archived_ones():
    info = ufgs.parse_api(API_ACTIVE)
    assert info["status"] is None  # nothing decided yet: ready to download
    assert info["pdf_url"] == ACTIVE_PDF_URL
    assert info["api_status"] == "ACTIVE"
    assert info["title"] == "UFGS 03 30 00 Cast-In-Place Concrete"
    assert info["publish_date"] == "2019-02-01T00:00:00.000Z"


def test_parse_api_retired():
    info = ufgs.parse_api(api_payload("33-32-13-13", status="RETIRED_SUPERSEDED"))
    assert info["status"] == "retired"
    assert info["pdf_url"] is None


def test_parse_api_active_without_current_pdf_is_no_pdf():
    payload = copy.deepcopy(API_ACTIVE)
    for m in payload["data"]["mediaFiles"]:
        if m["fileName"].endswith(".pdf"):
            m["isCurrent"] = False
    assert ufgs.parse_api(payload)["status"] == "no_pdf"


def test_parse_api_two_current_pdfs_is_error_not_a_guess():
    info = ufgs.parse_api(api_payload("03-30-00", pdf_urls=["https://a/1.pdf", "https://a/2.pdf"]))
    assert info["status"] == "error"
    assert "2 current PDFs" in info["error"]
    assert info["pdf_url"] is None


def test_parse_api_success_false_is_not_found():
    assert ufgs.parse_api({"success": False, "data": None})["status"] == "not_found"


@pytest.mark.parametrize("payload", [{"success": True}, {"success": True, "data": {"title": "x"}}])
def test_parse_api_unexpected_shape_is_error(payload):
    info = ufgs.parse_api(payload)
    assert info["status"] == "error"
    assert "Unexpected API answer" in info["error"]


# --- downloading --------------------------------------------------------------------------


def test_download_uses_the_api_file_url_and_writes_pdf_with_sha256(tmp_path):
    s = section("03-30-00")
    client, session, _ = make_client(
        {s.api_url: [api_json(API_ACTIVE)], ACTIVE_PDF_URL: [FakeResponse(200, PDF_BYTES)]}
    )

    entry = ufgs.download_section(client, s, tmp_path)

    path = ufgs.local_path(tmp_path, s)
    assert session.calls == [s.api_url, ACTIVE_PDF_URL]
    assert entry["status"] == "downloaded"
    assert entry["pdf_url"] == ACTIVE_PDF_URL
    assert entry["title"] == "UFGS 03 30 00 Cast-In-Place Concrete"
    assert entry["api_status"] == "ACTIVE"
    assert path.read_bytes() == PDF_BYTES
    assert entry["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert entry["bytes"] == len(PDF_BYTES)
    assert not path.with_name(path.name + ".part").exists()


def test_retired_section_makes_no_pdf_request(tmp_path):
    s = section("33-32-13-13")
    client, session, _ = make_client(
        {s.api_url: [api_json(api_payload(s.section_id, status="RETIRED_SUPERSEDED"))]}
    )

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "retired"
    assert entry["api_status"] == "RETIRED_SUPERSEDED"
    assert session.calls == [s.api_url]
    assert not ufgs.local_path(tmp_path, s).exists()


def test_api_404_is_not_found_and_not_retried(tmp_path):
    s = section("99-99-99")
    client, session, _ = make_client({})  # every URL answers 404

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "not_found"
    assert entry["http_status"] == 404
    assert session.calls == [s.api_url]


def test_api_answer_that_is_not_json_is_error(tmp_path):
    s = section("03-30-00")
    client, _, _ = make_client({s.api_url: [FakeResponse(200, b"<html>maintenance</html>")]})

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "error"
    assert "JSON" in entry["error"]


def test_pdf_403_after_active_api_answer_is_error(tmp_path):
    # The API promised a current PDF, so a missing file is a real problem, not "not found"
    s = section("03-30-00")
    client, _, _ = make_client(active_routes(s.section_id, [FakeResponse(403)]))

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "error"
    assert entry["http_status"] == 403


def test_503_is_retried_then_succeeds(tmp_path):
    s = section("03-30-00")
    client, session, sleeps = make_client(
        active_routes(s.section_id, [FakeResponse(503), FakeResponse(200, PDF_BYTES)])
    )

    entry = ufgs.download_section(client, s, tmp_path)

    assert entry["status"] == "downloaded"
    assert session.calls.count(pdf_url_for(s.section_id)) == 2
    assert 0.5 in sleeps  # backoff before the retry


def test_connection_error_is_retried(tmp_path):
    s = section("03-30-00")
    client, session, _ = make_client(
        active_routes(
            s.section_id, [requests.ConnectionError("boom"), FakeResponse(200, PDF_BYTES)]
        )
    )

    assert ufgs.download_section(client, s, tmp_path)["status"] == "downloaded"
    assert session.calls.count(pdf_url_for(s.section_id)) == 2


def test_non_pdf_body_is_rejected_and_leaves_no_file(tmp_path):
    s = section("03-30-00")
    client, _, _ = make_client(
        active_routes(s.section_id, [FakeResponse(200, b"<html>error</html>")])
    )

    entry = ufgs.download_section(client, s, tmp_path)

    path = ufgs.local_path(tmp_path, s)
    assert entry["status"] == "error"
    assert "PDF" in entry["error"]
    assert not path.exists()
    assert not path.with_name(path.name + ".part").exists()


def test_existing_active_pdf_is_skipped_after_api_check_and_force_redownloads(tmp_path):
    s = section("03-30-00")
    path = ufgs.local_path(tmp_path, s)
    path.parent.mkdir(parents=True)
    path.write_bytes(PDF_BYTES)
    client, session, _ = make_client(active_routes(s.section_id))

    entry = ufgs.download_section(client, s, tmp_path)
    assert entry["status"] == "skipped"
    assert entry["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert session.calls == [s.api_url]  # API checked, PDF not downloaded again

    assert ufgs.download_section(client, s, tmp_path, force=True)["status"] == "downloaded"
    assert session.calls[-1] == pdf_url_for(s.section_id)


def test_delay_between_requests():
    client, _, sleeps = make_client({"https://x/a": [FakeResponse(200)]})
    client.get("https://x/a")
    client.get("https://x/a")
    client.get("https://x/a")
    assert sleeps == [1.0, 1.0]  # no wait before the first request


# --- full run -----------------------------------------------------------------------------


def _run_routes():
    retired = section("33-32-13-13")
    return {
        ufgs.SITEMAP_URL: [FakeResponse(200, SITEMAP.encode())],
        **active_routes("01-33-00"),
        **active_routes("01-45-00-15-10"),
        retired.api_url: [api_json(api_payload(retired.section_id, status="RETIRED_SUPERSEDED"))],
    }


def test_run_writes_manifest_with_every_section(tmp_path):
    client, _, _ = make_client(_run_routes())

    manifest = ufgs.run(client, ["01", "33"], tmp_path)

    on_disk = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest
    ids = [e["section_id"] for e in manifest["sections"]]
    assert ids == ["01-33-00", "01-45-00-15-10", "33-32-13-13"]
    assert manifest["counts"] == {
        "downloaded": 2, "skipped": 0, "retired": 1, "no_pdf": 0, "not_found": 0, "error": 0,
    }  # fmt: skip
    assert manifest["divisions"] == ["01", "33"]


def test_run_deletes_a_retired_pdf_left_on_disk(tmp_path):
    retired = section("33-32-13-13")
    old = ufgs.local_path(tmp_path, retired)
    old.parent.mkdir(parents=True)
    old.write_bytes(PDF_BYTES)
    neighbour = old.with_name("my_notes.pdf")  # not ours: must survive
    neighbour.write_bytes(PDF_BYTES)
    client, _, _ = make_client(_run_routes())

    manifest = ufgs.run(client, ["33"], tmp_path)

    assert not old.exists()
    assert neighbour.exists()
    assert manifest["sections"][0]["removed"] is True
    assert manifest["removed"] == 1


def test_keep_retired_leaves_the_file(tmp_path):
    retired = section("33-32-13-13")
    old = ufgs.local_path(tmp_path, retired)
    old.parent.mkdir(parents=True)
    old.write_bytes(PDF_BYTES)
    client, _, _ = make_client(_run_routes())

    manifest = ufgs.run(client, ["33"], tmp_path, keep_retired=True)

    assert old.exists()
    assert manifest["sections"][0]["removed"] is False
    assert manifest["removed"] == 0


def test_second_run_skips_everything_and_keeps_download_time(tmp_path):
    client, _, _ = make_client(_run_routes())
    first = ufgs.run(client, ["01"], tmp_path)
    client, session, _ = make_client(_run_routes())

    second = ufgs.run(client, ["01"], tmp_path)

    assert second["counts"]["skipped"] == 2
    assert session.calls == [
        ufgs.SITEMAP_URL,
        section("01-33-00").api_url,
        section("01-45-00-15-10").api_url,
    ]
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
def test_real_api_answer_still_has_the_shape_we_parse():
    response = PoliteClient().get(section("03-30-00").api_url)
    info = ufgs.parse_api(response.json())

    assert info["api_status"] == "ACTIVE", info
    assert info["status"] is None, info
    assert info["pdf_url"].endswith("/FFC/DOD/UFGS/UFGS%2003%2030%2000.pdf")


@pytest.mark.network
def test_real_download_of_one_verified_section(tmp_path):
    entry = ufgs.download_section(PoliteClient(), section("01-33-00"), tmp_path)

    assert entry["status"] == "downloaded", entry
    assert ufgs.local_path(tmp_path, section("01-33-00")).read_bytes()[:4] == b"%PDF"
    assert len(entry["sha256"]) == 64
    # The name rule (kept for local file names) still matches WBDG's real file name
    assert entry["pdf_url"].endswith("UFGS%2001%2033%2000.pdf")
