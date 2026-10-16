"""Checksums of the raw data. Spec: specs/2026-10-16-data-catalog/spec.md.

All tests build a tiny fake `data/raw/` in a temporary folder; CI has no real data.
"""

import hashlib
import json
from pathlib import Path

import pytest

from src.datasets import checksums


def _make_raw(root: Path) -> None:
    """A small tree that looks like data/raw/: two datasets, an extra folder and skipped files."""
    files = {
        "ufgs/01/UFGS_01_11_00.pdf": b"%PDF-1.7 summary of work",
        "ufgs/manifest.json": b"{}",  # download record: skipped
        "ufgs/.gitkeep": b"",  # skipped
        "project_controls/ghent/DSLIB3.4.zip": b"PK\x03\x04 zip bytes",
        "project_controls/ghent/DSLIB 3.4/A/project 1.xlsx": b"xlsx bytes",
        "project_controls/ghent/download.json": b"{}",  # skipped
        "pid/dataset_pid/0/0_symbols.npy": b"\x93NUMPY",
        "pid/dataset_pid/drive_listing.json": b"[]",  # skipped
        "pid/dataset_pid/image_2.tar.gz.part": b"half",  # unfinished download: skipped
        "osha/notes.txt": b"other data",
    }
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


@pytest.fixture
def raw(tmp_path: Path) -> Path:
    root = tmp_path / "raw"
    _make_raw(root)
    return root


@pytest.fixture
def out(tmp_path: Path) -> Path:
    return tmp_path / "checksums.json"


def test_scan_lists_data_files_with_size_and_sha256(raw):
    entries = checksums.scan(raw)
    assert sorted(entries) == [
        "osha/notes.txt",
        "pid/dataset_pid/0/0_symbols.npy",
        "project_controls/ghent/DSLIB 3.4/A/project 1.xlsx",
        "project_controls/ghent/DSLIB3.4.zip",
        "ufgs/01/UFGS_01_11_00.pdf",
    ]
    pdf = b"%PDF-1.7 summary of work"
    assert entries["ufgs/01/UFGS_01_11_00.pdf"] == {
        "bytes": len(pdf),
        "sha256": hashlib.sha256(pdf).hexdigest(),
    }


def test_keys_use_forward_slashes(raw):
    assert all("\\" not in key for key in checksums.scan(raw))


def test_dataset_of_maps_paths_to_dataset_names():
    assert checksums.dataset_of("ufgs/01/a.pdf") == "ufgs"
    assert checksums.dataset_of("project_controls/ghent/x.zip") == "ghent"
    assert checksums.dataset_of("pid/pid2graph/PID2Graph.zip") == "pid2graph"
    assert checksums.dataset_of("pid/dataset_pid/0/0_lines.npy") == "dataset_pid"
    assert checksums.dataset_of("osha/notes.txt") == "other"


def test_sha256_file_reads_in_chunks(tmp_path):
    data = bytes(range(256)) * 10_000  # bigger than one chunk
    path = tmp_path / "big.bin"
    path.write_bytes(data)
    assert checksums.sha256_file(path, chunk_size=1000) == hashlib.sha256(data).hexdigest()


def test_write_creates_file_with_totals(raw, out):
    doc = checksums.write(raw, out)
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved == doc
    assert saved["algorithm"] == "sha256"
    assert "updated_at" in saved
    assert saved["datasets"]["ufgs"]["files"] == 1
    assert saved["datasets"]["ghent"]["files"] == 2
    assert saved["datasets"]["other"]["files"] == 1
    assert saved["datasets"]["ghent"]["bytes"] == sum(
        e["bytes"] for k, e in saved["files"].items() if k.startswith("project_controls/ghent/")
    )
    assert list(saved["files"]) == sorted(saved["files"])


def test_second_write_without_changes_leaves_file_identical(raw, out):
    checksums.write(raw, out)
    first = out.read_bytes()
    checksums.write(raw, out)
    assert out.read_bytes() == first


def test_write_one_dataset_keeps_the_others(raw, out):
    checksums.write(raw, out)
    (raw / "ufgs/01/UFGS_01_11_00.pdf").write_bytes(b"%PDF new version")
    (raw / "project_controls/ghent/DSLIB3.4.zip").write_bytes(b"changed, but not rescanned")
    before = json.loads(out.read_text(encoding="utf-8"))

    checksums.write(raw, out, dataset="ufgs")
    after = json.loads(out.read_text(encoding="utf-8"))

    pdf = "ufgs/01/UFGS_01_11_00.pdf"
    assert after["files"][pdf]["sha256"] == hashlib.sha256(b"%PDF new version").hexdigest()
    ghent_zip = "project_controls/ghent/DSLIB3.4.zip"
    assert after["files"][ghent_zip] == before["files"][ghent_zip]


def test_write_one_dataset_drops_its_deleted_files(raw, out):
    checksums.write(raw, out)
    (raw / "ufgs/01/UFGS_01_11_00.pdf").unlink()
    checksums.write(raw, out, dataset="ufgs")
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert "ufgs/01/UFGS_01_11_00.pdf" not in saved["files"]
    assert "ufgs" not in saved["datasets"]


def test_verify_all_ok(raw, out):
    checksums.write(raw, out)
    report = checksums.verify(raw, out)
    assert report.ok == 5
    assert (report.missing, report.changed, report.new) == ([], [], [])
    assert report.passed


def test_verify_finds_a_changed_byte(raw, out):
    checksums.write(raw, out)
    path = raw / "ufgs/01/UFGS_01_11_00.pdf"
    data = bytearray(path.read_bytes())
    data[0] ^= 1  # same size, one bit different
    path.write_bytes(bytes(data))
    report = checksums.verify(raw, out)
    assert report.changed == ["ufgs/01/UFGS_01_11_00.pdf"]
    assert not report.passed


def test_verify_finds_a_missing_file(raw, out):
    checksums.write(raw, out)
    (raw / "osha/notes.txt").unlink()
    report = checksums.verify(raw, out)
    assert report.missing == ["osha/notes.txt"]
    assert not report.passed


def test_verify_new_file_is_only_a_warning(raw, out):
    checksums.write(raw, out)
    (raw / "ufgs/01/extra.pdf").write_bytes(b"%PDF extra")
    report = checksums.verify(raw, out)
    assert report.new == ["ufgs/01/extra.pdf"]
    assert report.passed


def test_verify_ignores_skipped_files(raw, out):
    checksums.write(raw, out)
    (raw / "ufgs/manifest.json").write_text('{"changed": true}', encoding="utf-8")
    (raw / "pid/dataset_pid/mask.tar.gz.part").write_bytes(b"more")
    report = checksums.verify(raw, out)
    assert (report.missing, report.changed, report.new) == ([], [], [])


def test_quick_verify_compares_sizes_only(raw, out):
    checksums.write(raw, out)
    path = raw / "ufgs/01/UFGS_01_11_00.pdf"
    data = bytearray(path.read_bytes())
    data[0] ^= 1  # same size: quick mode cannot see it
    path.write_bytes(bytes(data))
    assert checksums.verify(raw, out, quick=True).passed

    path.write_bytes(b"different length")
    assert checksums.verify(raw, out, quick=True).changed == ["ufgs/01/UFGS_01_11_00.pdf"]


def test_verify_one_dataset(raw, out):
    checksums.write(raw, out)
    (raw / "osha/notes.txt").unlink()  # not part of the checked dataset
    report = checksums.verify(raw, out, dataset="ghent")
    assert report.ok == 2
    assert report.passed


def test_verify_without_checksum_file_fails_clearly(raw, out):
    with pytest.raises(FileNotFoundError, match="--write"):
        checksums.verify(raw, out)


def test_cli_exit_codes(raw, out, capsys):
    args = ["--root", str(raw), "--out", str(out)]
    assert checksums.main(["--write", *args]) == 0
    assert checksums.main(["--verify", *args]) == 0
    (raw / "osha/notes.txt").unlink()
    assert checksums.main(["--verify", *args]) == 1
    assert "missing (1)" in capsys.readouterr().out


def test_cli_rejects_quick_with_write(raw, out):
    with pytest.raises(SystemExit):
        checksums.main(["--write", "--quick", "--root", str(raw), "--out", str(out)])
