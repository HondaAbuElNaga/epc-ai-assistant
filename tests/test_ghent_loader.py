"""Ghent DSLIB loader. Spec: specs/2026-10-08-ghent-project-db/spec.md ("Table columns").

All tests run on the fake DSLIB folder from tests/fixtures/ghent_fixture.py (made-up values in
the real layout); no real data is needed.
"""

import math
import re

import pandas as pd
import pytest

from src.datasets import ghent
from tests.fixtures.ghent_fixture import build_dslib


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    return ghent.load_ghent(build_dslib(tmp_path_factory.mktemp("ghent")))


def _row(df, **where):
    mask = pd.Series(True, index=df.index)
    for col, value in where.items():
        mask &= df[col] == value
    rows = df[mask]
    assert len(rows) == 1, f"expected 1 row for {where}, got {len(rows)}"
    return rows.iloc[0]


# --- helpers --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("C2011-05 Telecom System Agnes.xlsx", "C2011-05"),
        ("C2016-9 Railway Bridge.pdf", "C2016-09"),
        ("C2019-11_procard.pdf", "C2019-11"),
        ("C2016-31Apartment Building.pdf", "C2016-31"),
        ("C2025-01.p2x", "C2025-01"),
    ],
)
def test_normalize_project_id(text, expected):
    assert ghent.normalize_project_id(text) == expected


def test_normalize_project_id_rejects_other_names():
    with pytest.raises(ValueError):
        ghent.normalize_project_id("Readme.rtf")


@pytest.mark.parametrize(
    ("value", "days", "hours"),
    [
        ("3d", 3, 0),
        ("4h", 0, 4),
        ("1d 2h", 1, 2),
        ("1d4h", 1, 4),
        ("4d 11h ", 4, 11),
        ("58 days", 58, 0),
        ("1 day", 1, 0),
        ("0", 0, 0),
        ("766d", 766, 0),
    ],
)
def test_parse_duration(value, days, hours):
    assert ghent.parse_duration(value) == (days, hours)


@pytest.mark.parametrize("value", [None, "", "soon"])
def test_parse_duration_unknown_is_nan(value):
    days, hours = ghent.parse_duration(value)
    assert math.isnan(days) and math.isnan(hours)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1210, 1210.0),
        (4679795.5, 4679795.5),
        ("€743 676", 743676.0),
        ("€\xa0464 186,97", 464186.97),
    ],
)
def test_parse_euro(value, expected):
    assert ghent.parse_euro(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", [None, "-", "N/A", ""])
def test_parse_euro_missing_markers_are_nan(value):
    assert math.isnan(ghent.parse_euro(value))


# --- table shape ----------------------------------------------------------------------------


def test_returns_four_tables_with_spec_columns(data):
    assert list(data.projects.columns) == ghent.PROJECT_COLUMNS
    assert list(data.activities.columns) == ghent.ACTIVITY_COLUMNS
    assert list(data.tracking.columns) == ghent.TRACKING_COLUMNS
    assert list(data.issues.columns) == ghent.ISSUE_COLUMNS


def test_column_names_are_snake_case(data):
    for df in (data.projects, data.activities, data.tracking, data.issues):
        for col in df.columns:
            assert re.fullmatch(r"[a-z][a-z0-9_]*", col), col


# --- projects -------------------------------------------------------------------------------


def test_projects_one_row_per_project_without_summary_rows(data):
    assert sorted(data.projects["project_id"]) == ["C2011-05", "C2012-03", "C2023-01"]


def test_projects_group(data):
    groups = dict(zip(data.projects["project_id"], data.projects["group"], strict=True))
    assert groups == {"C2011-05": "A", "C2023-01": "B", "C2012-03": "C"}


def test_projects_money_and_numbers(data):
    p = data.projects
    assert _row(p, project_id="C2011-05")["bac"] == 1300.0
    assert _row(p, project_id="C2023-01")["bac"] == 743676.0  # "€743 676"
    assert math.isnan(_row(p, project_id="C2012-03")["bac"])  # "-"
    assert _row(p, project_id="C2012-03")["real_cost"] == pytest.approx(464186.97)
    assert _row(p, project_id="C2011-05")["planned_duration_days"] == 10.0
    assert _row(p, project_id="C2011-05")["duration_deviation"] == pytest.approx(0.1)
    assert math.isnan(_row(p, project_id="C2023-01")["ri"])  # "N/A"
    assert pd.api.types.is_float_dtype(p["bac"])


def test_projects_text_cleaning(data):
    p = data.projects
    assert set(p["sector"]) == {"IT", "Construction (civil)"}  # "(Civil)" and "(civil)" unified
    assert _row(p, project_id="C2011-05")["regularity"] == "irregular"
    assert pd.isna(_row(p, project_id="C2023-01")["regularity"])  # "N/A"
    assert _row(p, project_id="C2011-05")["has_resources"] is True
    assert _row(p, project_id="C2023-01")["has_resources"] is False
    assert _row(p, project_id="C2012-03")["has_resources"] is None
    assert _row(p, project_id="C2012-03")["excel_file"] == "C2012-3 Test Day Care.xlsx"


def test_projects_completeness_colours(data):
    p = data.projects
    cols = ["completeness_baseline", "completeness_risk", "completeness_control"]
    assert list(_row(p, project_id="C2011-05")[cols]) == ["green", "yellow", "green"]
    assert list(_row(p, project_id="C2023-01")[cols]) == ["yellow", "yellow", "orange"]
    assert list(_row(p, project_id="C2012-03")[cols]) == ["orange", "green", None]


# --- activities -----------------------------------------------------------------------------


def test_activities_exclude_project_row(data):
    a = data.activities
    assert 0 not in set(a["activity_id"])
    counts = a.groupby("project_id").size().to_dict()
    assert counts == {"C2011-05": 4, "C2012-03": 2, "C2023-01": 3}


def test_activities_types(data):
    a = data.activities
    assert pd.api.types.is_integer_dtype(a["activity_id"])  # text IDs "2" converted
    assert pd.api.types.is_datetime64_any_dtype(a["baseline_start"])
    assert pd.api.types.is_datetime64_any_dtype(a["baseline_end"])
    assert pd.api.types.is_float_dtype(a["total_cost"])
    assert pd.api.types.is_bool_dtype(a["is_summary"])


def test_activities_wbs_summary_rows_flagged(data):
    a = data.activities[data.activities["project_id"] == "C2011-05"]
    summary = dict(zip(a["activity_id"], a["is_summary"], strict=True))
    assert summary == {1: True, 2: False, 4: False, 3: False}
    leaves = a[~a["is_summary"]]
    assert leaves["total_cost"].sum() == 1300.0  # = project total on the ID 0 row


def test_activities_durations(data):
    a = data.activities
    install = _row(a, project_id="C2011-05", activity_id=3)
    assert (install["duration_raw"], install["duration_days"], install["duration_hours"]) == (
        "1d 2h",
        1,
        2,
    )
    scaffolding = _row(a, project_id="C2023-01", activity_id=2)
    assert (scaffolding["duration_days"], scaffolding["duration_hours"]) == (58, 0)
    assert _row(a, project_id="C2011-05", activity_id=2)["calendar_days"] == 2.375


def test_activities_relations_and_successors_typo(data):
    a = data.activities
    assert _row(a, project_id="C2011-05", activity_id=3)["predecessors"] == "2FS;4FS"
    assert _row(a, project_id="C2012-03", activity_id=1)["successors"] == "FS2"  # "Sussessors"


def test_activities_missing_optional_columns_are_empty(data):
    b = data.activities[data.activities["project_id"] == "C2023-01"]
    assert b["baseline_end"].isna().all()
    assert b["total_cost"].isna().all()
    assert b["calendar_days"].isna().all()
    assert set(b["fixed_cost"]) == {5000.0, 2000.0, 0.0}


def test_activities_duplicate_ids_kept_and_reported(data):
    b = data.activities[data.activities["project_id"] == "C2023-01"]
    assert list(b["activity_id"]).count(3) == 2
    issue = _row(data.issues, project_id="C2023-01", problem="duplicate activity_id 3")
    assert issue["table"] == "activities"


# --- tracking -------------------------------------------------------------------------------


def test_tracking_only_group_a(data):
    assert set(data.tracking["project_id"]) == {"C2011-05"}


def test_tracking_values(data):
    t = data.tracking
    assert list(t["period"]) == [1, 2]
    assert list(t["is_final"]) == [False, True]
    first = t.iloc[0]
    assert first["period_name"] == "06/05, 2011"
    assert first["status_date"] == pd.Timestamp(2011, 5, 6, 17)
    assert (first["pv"], first["ev"], first["ac"]) == (800.0, 700.0, 750.0)
    assert (first["spi"], first["cpi"], first["spi_t"], first["p_factor"]) == (
        0.875,
        0.9333,
        0.9,
        0.95,
    )
    assert first["sv_t_raw"] == "-1d 4h"
    assert first["es"] == pd.Timestamp(2011, 5, 5, 12)
    assert pd.api.types.is_datetime64_any_dtype(t["status_date"])


# --- issues and errors ----------------------------------------------------------------------


def test_missing_bac_is_reported(data):
    assert _row(data.issues, project_id="C2012-03", problem="BAC missing")["table"] == "projects"


def test_missing_required_column_raises_clear_error(tmp_path):
    dslib = build_dslib(tmp_path, drop_baseline_column="Duration")
    with pytest.raises(ghent.GhentFormatError) as err:
        ghent.load_ghent(dslib)
    message = str(err.value)
    assert "C2011-05 Test Telecom.xlsx" in message
    assert "Duration" in message


def test_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ghent.load_ghent(tmp_path / "nowhere")
