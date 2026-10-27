"""Integrity of the real data in data/raw/: folders, file sizes, UFGS PDFs, Ghent numbers.

Spec: specs/2026-10-24-data-integrity/spec.md

Local only (CI has no data): `uv run pytest -m data`. Run it alone, not next to another heavy
job. A missing dataset fails, it does not skip. Overrides for testing the tests:
EPC_RAW_DIR (data root) and EPC_CHECKSUMS (checksum file).
"""

import json
import os
from pathlib import Path

import pytest

from src.datasets import checksums
from src.datasets.ghent import load_ghent
from src.datasets.profiling import pdf_stats

pytestmark = [
    pytest.mark.data,
    # openpyxl warns about an Excel extension in some DSLIB workbooks; harmless here
    pytest.mark.filterwarnings("ignore:Unknown extension is not supported:UserWarning"),
]

RAW_DIR = Path(os.getenv("EPC_RAW_DIR", checksums.RAW_DIR))
CHECKSUMS = Path(os.getenv("EPC_CHECKSUMS", checksums.OUT_FILE))

# Expected numbers from data/DATA_CATALOG.md (UFGS and Ghent sections); file counts per dataset
# come from checksums.json. If the data is re-downloaded and these change, update the docs too.
UFGS_PDFS = 271
UFGS_DIVISIONS = {"01", "03", "05", "22", "23", "26", "33", "40", "41", "43", "44", "46"}
GHENT_PROJECTS = 231
GHENT_GROUPS = {"A": 117, "B": 41, "C": 73}


@pytest.fixture(scope="module")
def recorded() -> dict:
    return json.loads(CHECKSUMS.read_text(encoding="utf-8"))["datasets"]


@pytest.fixture(scope="module")
def report() -> checksums.Report:
    # One size-only verify for all datasets: walking data/raw/ is the slow part (~30 s)
    # Full SHA-256: python -m src.datasets.checksums --verify
    return checksums.verify(RAW_DIR, CHECKSUMS, quick=True)


def _of(dataset: str, keys: list[str]) -> list[str]:
    return [key for key in keys if checksums.dataset_of(key) == dataset]


@pytest.fixture(scope="module")
def ghent():
    return load_ghent(RAW_DIR / "project_controls" / "ghent" / "DSLIB 3.4")


# --- folders and checksums -------------------------------------------------------------------


@pytest.mark.parametrize("dataset", sorted(checksums.DATASETS))
def test_folder_has_recorded_file_count(dataset, recorded, report):
    folder = RAW_DIR / checksums.DATASETS[dataset]
    assert folder.is_dir(), f"{dataset}: folder {folder} not found"
    expected = recorded[dataset]["files"]
    missing = len(_of(dataset, report.missing))
    on_disk = expected - missing + len(_of(dataset, report.new))
    assert on_disk == recorded[dataset]["files"], (
        f"{dataset}: {on_disk} files on disk, {expected} in {CHECKSUMS.name}"
    )


@pytest.mark.parametrize("dataset", sorted(checksums.DATASETS))
def test_sizes_match_checksums(dataset, report):
    missing, changed = _of(dataset, report.missing), _of(dataset, report.changed)
    assert not missing, f"{dataset}: missing files: {missing[:20]}"
    assert not changed, f"{dataset}: size changed: {changed[:20]}"


# --- UFGS PDFs -------------------------------------------------------------------------------


def test_ufgs_pdfs_open_with_text_on_every_page():
    pdfs = sorted((RAW_DIR / "ufgs").glob("*/*.pdf"))
    assert len(pdfs) == UFGS_PDFS
    assert {pdf.parent.name for pdf in pdfs} == UFGS_DIVISIONS
    bad = []
    for pdf in pdfs:
        name = pdf.relative_to(RAW_DIR).as_posix()
        try:
            stats = pdf_stats(pdf)
        except Exception as error:  # any read error is a bad file; list them all
            bad.append(f"{name}: cannot open ({error})")
            continue
        if stats["pages"] < 1:
            bad.append(f"{name}: no pages")
        elif stats["empty_pages"]:
            bad.append(f"{name}: {stats['empty_pages']} page(s) without text")
    assert not bad, "bad UFGS PDFs:\n" + "\n".join(bad)


# --- Ghent DSLIB ----------------------------------------------------------------------------


def test_ghent_project_and_group_counts(ghent):
    projects = ghent.projects
    assert len(projects) == GHENT_PROJECTS
    assert projects["project_id"].is_unique
    assert projects["group"].value_counts().to_dict() == GHENT_GROUPS


def test_ghent_every_project_has_activities(ghent):
    without = set(ghent.projects["project_id"]) - set(ghent.activities["project_id"])
    assert not without, f"projects without activities: {sorted(without)}"


def test_ghent_group_a_has_tracking(ghent):
    # Only group A has tracking periods in DSLIB 3.4 (B and C have none)
    group_a = set(ghent.projects.loc[ghent.projects["group"] == "A", "project_id"])
    without = group_a - set(ghent.tracking["project_id"])
    assert not without, f"group A projects without tracking: {sorted(without)}"


def test_ghent_bac_positive_and_present_for_group_a(ghent):
    projects = ghent.projects
    bac = projects["bac"]
    assert (bac.dropna() > 0).all(), "BAC <= 0 for some projects"
    missing_a = projects.loc[(projects["group"] == "A") & bac.isna(), "project_id"]
    assert missing_a.empty, f"group A projects without BAC: {sorted(missing_a)}"
