"""P&ID dataset downloader. Spec: specs/2026-10-14-pid-datasets/spec.md.

All tests are offline: a fake HTTP session serves the responses, and the archives are tiny ones
built in the test. The Drive fixtures are trimmed copies of the real folder-view pages.
"""

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from src.common.http import PoliteClient
from src.datasets import pid

FIXTURES = Path(__file__).parent / "fixtures"
ROOT_HTML = (FIXTURES / "drive_folder_root.html").read_text(encoding="utf-8")
FOLDER0_HTML = (FIXTURES / "drive_folder_0.html").read_text(encoding="utf-8")
# Real IDs from the fixtures
FOLDER0_ID = "1-Gc_1OTWcoEoxsdKfmhgnrdz-VuvPl7y"
FOLDER1_ID = "1UBI9yy4rOTF7Fu1ORzF9gHjcwBoThdNq"
IMAGE2_ID = "1VvhnjFVOR7gdgJFQv8PjWgYzj4pAzdMa"

URL = "https://example.org/file.bin"
DATA = bytes(range(256)) * 40  # 10,240 bytes
DATA_MD5 = hashlib.md5(DATA).hexdigest()


class FakeResponse:
    def __init__(self, status_code=200, body=b"", headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = {"Content-Type": "application/octet-stream", **(headers or {})}
        self.text = body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]

    def close(self):
        pass


class FakeSession:
    """Answers each URL with a handler (a response, or a function of the request headers).
    Records every call as (url, headers)."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []
        self.headers = {}

    def get(self, url, headers=None, **kwargs):
        headers = headers or {}
        self.calls.append((url, headers))
        handler = self.routes.get(url)
        if handler is None:
            return FakeResponse(404, b"not found", {"Content-Type": "text/html"})
        return handler(headers) if callable(handler) else handler

    def urls(self):
        return [url for url, _ in self.calls]


def client(routes):
    session = FakeSession(routes)
    return PoliteClient(session, delay=0, sleep=lambda s: None), session


def ranged(data):
    """A server that honours `Range: bytes=N-`."""

    def handler(headers):
        rng = headers.get("Range")
        if not rng:
            return FakeResponse(200, data)
        start = int(rng.removeprefix("bytes=").rstrip("-"))
        if start >= len(data):
            return FakeResponse(416, b"")
        cr = f"bytes {start}-{len(data) - 1}/{len(data)}"
        return FakeResponse(206, data[start:], {"Content-Range": cr})

    return handler


# --- Drive folder-view parser ----------------------------------------------------------------


def test_parse_drive_root_folder():
    entries = pid.parse_drive_folder(ROOT_HTML)
    assert [(e.name, e.is_folder) for e in entries] == [
        ("0", True),
        ("1", True),
        ("image_2.tar.gz", False),
    ]
    assert entries[0].id == FOLDER0_ID
    assert entries[2].id == IMAGE2_ID


def test_parse_drive_subfolder_lists_seven_npy_files():
    entries = pid.parse_drive_folder(FOLDER0_HTML)
    names = sorted(e.name for e in entries)
    assert names == sorted(f"0_{kind}.npy" for kind in pid.NPY_KINDS)
    assert not any(e.is_folder for e in entries)
    assert all(e.id for e in entries)


def test_parse_drive_page_without_entries_is_empty():
    assert pid.parse_drive_folder("<html><body>Sign in</body></html>") == []


# --- Zenodo record ---------------------------------------------------------------------------


def zenodo_payload(size, md5, key=pid.PID2GRAPH_ZIP):
    return {
        "doi": "10.5281/zenodo.14803338",
        "metadata": {"publication_date": "2025-02-14", "license": {"id": "cc-by-sa-4.0"}},
        "files": [
            {
                "key": key,
                "size": size,
                "checksum": f"md5:{md5}",
                "links": {"self": f"https://zenodo.org/files/{key}/content"},
            }
        ],
    }


def test_zenodo_file_reads_url_size_md5():
    remote = pid.zenodo_file(zenodo_payload(123, "abc"), pid.PID2GRAPH_ZIP)
    assert remote == pid.RemoteFile(
        url="https://zenodo.org/files/PID2Graph.zip/content", size=123, md5="abc"
    )


def test_zenodo_file_missing_key_raises():
    with pytest.raises(pid.DownloadError, match="PID2Graph.zip"):
        pid.zenodo_file(zenodo_payload(1, "x", key="other.zip"), pid.PID2GRAPH_ZIP)


# --- download(): fresh, resume, verify, skip -------------------------------------------------


def test_download_fresh_file_is_verified_and_renamed(tmp_path):
    c, _ = client({URL: ranged(DATA)})
    dest = tmp_path / "file.bin"
    result = pid.download(c, URL, dest, size=len(DATA), md5=DATA_MD5)
    assert result.status == "downloaded"
    assert dest.read_bytes() == DATA
    assert result.bytes == len(DATA)
    assert result.md5 == DATA_MD5
    assert result.sha256 == hashlib.sha256(DATA).hexdigest()
    assert not (tmp_path / "file.bin.part").exists()


def test_download_resumes_from_part_file_with_range(tmp_path):
    dest = tmp_path / "file.bin"
    (tmp_path / "file.bin.part").write_bytes(DATA[:4000])
    c, session = client({URL: ranged(DATA)})
    result = pid.download(c, URL, dest, size=len(DATA), md5=DATA_MD5)
    assert session.calls[0][1].get("Range") == "bytes=4000-"
    assert dest.read_bytes() == DATA
    assert result.md5 == DATA_MD5  # the hash covers the resumed part too


def test_download_restarts_when_server_ignores_range(tmp_path):
    dest = tmp_path / "file.bin"
    (tmp_path / "file.bin.part").write_bytes(DATA[:4000])
    c, _ = client({URL: FakeResponse(200, DATA)})  # 200 = full file, Range ignored
    pid.download(c, URL, dest, size=len(DATA), md5=DATA_MD5)
    assert dest.read_bytes() == DATA


def test_download_complete_part_file_is_finished_without_body(tmp_path):
    dest = tmp_path / "file.bin"
    (tmp_path / "file.bin.part").write_bytes(DATA)  # stopped just before the rename
    c, _ = client({URL: ranged(DATA)})  # answers 416: nothing left to send
    result = pid.download(c, URL, dest, size=len(DATA), md5=DATA_MD5)
    assert result.status == "downloaded"
    assert dest.read_bytes() == DATA


def test_download_md5_mismatch_raises_and_keeps_no_file(tmp_path):
    c, _ = client({URL: ranged(DATA)})
    dest = tmp_path / "file.bin"
    with pytest.raises(pid.DownloadError, match="MD5"):
        pid.download(c, URL, dest, size=len(DATA), md5="0" * 32)
    assert not dest.exists()
    assert not (tmp_path / "file.bin.part").exists()


def test_download_size_mismatch_raises_and_keeps_no_file(tmp_path):
    c, _ = client({URL: ranged(DATA[:-1])})
    dest = tmp_path / "file.bin"
    with pytest.raises(pid.DownloadError, match="size"):
        pid.download(c, URL, dest, size=len(DATA))
    assert not dest.exists()
    assert not (tmp_path / "file.bin.part").exists()


def test_download_skips_existing_file(tmp_path):
    dest = tmp_path / "file.bin"
    dest.write_bytes(DATA)
    c, session = client({URL: ranged(DATA)})
    result = pid.download(c, URL, dest, size=len(DATA))
    assert result.status == "skipped"
    assert session.calls == []


def test_download_existing_file_with_wrong_size_is_downloaded_again(tmp_path):
    dest = tmp_path / "file.bin"
    dest.write_bytes(b"old")
    c, _ = client({URL: ranged(DATA)})
    assert pid.download(c, URL, dest, size=len(DATA)).status == "downloaded"
    assert dest.read_bytes() == DATA


def test_download_html_page_instead_of_file_raises(tmp_path):
    page = FakeResponse(200, b"<html>quota exceeded</html>", {"Content-Type": "text/html"})
    c, _ = client({URL: page})
    with pytest.raises(pid.DownloadError, match="HTML"):
        pid.download(c, URL, tmp_path / "file.bin")
    assert not (tmp_path / "file.bin").exists()


def test_download_http_error_raises(tmp_path):
    c, _ = client({})
    with pytest.raises(pid.DownloadError, match="404"):
        pid.download(c, URL, tmp_path / "file.bin")


# --- Safe extraction -------------------------------------------------------------------------


def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)


def test_extract_zip_only_takes_the_prefix(tmp_path):
    zpath = tmp_path / "a.zip"
    make_zip(
        zpath,
        {
            "PID2Graph/Complete/OPEN100/1.png": b"img",
            "PID2Graph/Complete/OPEN100/1.graphml": b"<graphml/>",
            "PID2Graph/Patched/OPEN100/1_0.png": b"tile",
        },
    )
    out = tmp_path / "out"
    assert pid.extract_zip(zpath, out, "PID2Graph/Complete/") == 2
    assert (out / "PID2Graph/Complete/OPEN100/1.png").read_bytes() == b"img"
    assert not (out / "PID2Graph/Patched").exists()
    assert pid.extract_zip(zpath, out, "PID2Graph/Complete/") == 0  # second run: all there


@pytest.mark.parametrize(
    "bad_name",
    ["PID2Graph/Complete/../../evil.txt", "PID2Graph/Complete/..\\..\\evil.txt"],
)
def test_extract_zip_rejects_zip_slip_and_writes_nothing(tmp_path, bad_name):
    zpath = tmp_path / "a.zip"
    make_zip(zpath, {"PID2Graph/Complete/ok.png": b"ok", bad_name: b"evil"})
    out = tmp_path / "out"
    with pytest.raises(pid.UnsafeArchiveError, match="evil"):
        pid.extract_zip(zpath, out, "PID2Graph/Complete/")
    assert not (tmp_path / "evil.txt").exists()
    assert not (out / "PID2Graph/Complete/ok.png").exists()  # checked before extracting any


def make_tar_gz(members):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_extract_tar_into_its_own_folder(tmp_path):
    tpath = tmp_path / "image_2.tar.gz"
    tpath.write_bytes(make_tar_gz({"image_2/0.jpg": b"jpg"}))
    target = pid.extract_tar(tpath, tmp_path)
    assert target == tmp_path / "image_2"
    assert (target / "image_2/0.jpg").read_bytes() == b"jpg"
    assert not (tmp_path / "image_2.part").exists()


def test_extract_tar_rejects_path_outside_and_leaves_nothing(tmp_path):
    tpath = tmp_path / "bad.tar.gz"
    tpath.write_bytes(make_tar_gz({"../evil.txt": b"evil"}))
    with pytest.raises(tarfile.FilterError):
        pid.extract_tar(tpath, tmp_path / "out")
    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path / "out" / "bad").exists()
    assert not (tmp_path / "out" / "bad.part").exists()


# --- Dataset-P&ID completeness check ---------------------------------------------------------


def full_listing(n):
    return {
        "archives": {name: f"id-{name}" for name in pid.DRIVE_ARCHIVES},
        "folders": {
            str(i): {f"{i}_{k}.npy": f"id-{i}-{k}" for k in pid.NPY_KINDS} for i in range(n)
        },
    }


def test_check_listing_complete():
    assert pid.check_listing(full_listing(3), n_drawings=3) == {"missing": [], "extra": []}


def test_check_listing_reports_missing_and_extra():
    listing = full_listing(3)
    del listing["folders"]["1"]["1_words.npy"]
    del listing["folders"]["2"]
    listing["folders"]["0"]["notes.txt"] = "id-x"
    del listing["archives"]["mask.tar.gz"]
    result = pid.check_listing(listing, n_drawings=3)
    assert result["missing"] == ["1/1_words.npy", "2/", "mask.tar.gz"]
    assert result["extra"] == ["0/notes.txt"]


# --- End to end with fakes -------------------------------------------------------------------


def test_run_pid2graph_downloads_extracts_and_writes_manifest(tmp_path):
    zpath = tmp_path / "src.zip"
    make_zip(
        zpath,
        {
            "PID2Graph/Complete/PID2Graph OPEN100/1.png": b"img",
            "PID2Graph/Complete/PID2Graph OPEN100/1.graphml": b"<graphml/>",
            "PID2Graph/Patched/PID2Graph OPEN100/1_0.png": b"tile",
        },
    )
    zbytes = zpath.read_bytes()
    md5 = hashlib.md5(zbytes).hexdigest()
    zip_url = "https://zenodo.org/files/PID2Graph.zip/content"
    routes = {
        pid.ZENODO_API: FakeResponse(200, json.dumps(zenodo_payload(len(zbytes), md5)).encode()),
        zip_url: ranged(zbytes),
    }
    c, session = client(routes)
    out = tmp_path / "pid2graph"
    manifest = pid.run_pid2graph(c, out)

    assert manifest["file"]["md5"] == md5
    assert manifest["file"]["bytes"] == len(zbytes)
    assert manifest["license"] == "cc-by-sa-4.0"
    assert "Stürmer" in manifest["citation"]
    assert manifest["extracted"]["prefix"] == "PID2Graph/Complete/"
    assert manifest["counts"] == {"PID2Graph OPEN100": {".graphml": 1, ".png": 1}}
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8")) == manifest

    pid.run_pid2graph(c, out)  # second run: API asked again, zip not downloaded again
    assert session.urls().count(zip_url) == 1


def test_run_dataset_pid_downloads_lists_gaps_and_caches_listing(tmp_path):
    folder1_html = FOLDER0_HTML.replace(">0_", ">1_")  # same IDs, names of drawing 1
    image2 = make_tar_gz({"image_2/0.jpg": b"jpg"})
    routes = {
        pid.DRIVE_VIEW.format(pid.DRIVE_ROOT_ID): FakeResponse(200, ROOT_HTML.encode()),
        pid.DRIVE_VIEW.format(FOLDER0_ID): FakeResponse(200, FOLDER0_HTML.encode()),
        pid.DRIVE_VIEW.format(FOLDER1_ID): FakeResponse(200, folder1_html.encode()),
        pid.DRIVE_FILE.format(IMAGE2_ID): ranged(image2),
    }
    for entry in pid.parse_drive_folder(FOLDER0_HTML):
        routes[pid.DRIVE_FILE.format(entry.id)] = ranged(b"\x93NUMPY fake " + entry.id.encode())
    c, session = client(routes)
    out = tmp_path / "dataset_pid"
    manifest = pid.run_dataset_pid(c, out, n_drawings=2)

    assert (out / "0" / "0_symbols.npy").is_file()
    assert (out / "1" / "1_words.npy").is_file()
    assert (out / "image_2" / "image_2" / "0.jpg").read_bytes() == b"jpg"
    assert manifest["missing"] == ["mask.tar.gz"]  # not in the trimmed root fixture
    assert manifest["extra"] == []
    assert len(manifest["files"]) == 2 * 7 + 1
    assert all(len(f["sha256"]) == 64 for f in manifest["files"])
    assert (out / "drive_listing.json").is_file()

    calls_before = len(session.calls)
    pid.run_dataset_pid(c, out, n_drawings=2)  # second run: cached listing, all files skipped
    assert len(session.calls) == calls_before
