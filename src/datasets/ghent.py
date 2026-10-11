"""Load the Ghent DSLIB real project database into clean pandas tables.

Spec: specs/2026-10-08-ghent-project-db/spec.md · Format: format_notes.md in the same folder.

    python -m src.datasets.ghent [path/to/"DSLIB 3.4"]

`load_ghent()` reads the summary workbook (`DSLIB_Analysis_Sheet.xlsx`, one row per project)
and the per-project workbooks in `Excel/`, and returns four tables:

- `projects`   one row per project, with its group (A tracking ready, B raw progress only,
               C plan only)
- `activities` one row per baseline activity (the ID 0 project row is left out)
- `tracking`   one row per tracking period, from `Tracking Overview` (group A only)
- `issues`     every data problem found; problem rows are listed, never silently dropped
"""

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

import openpyxl
import pandas as pd

from src.common import config

DEFAULT_DIR = config.RAW_DIR / "project_controls" / "ghent" / "DSLIB 3.4"
ANALYSIS_FILE = "DSLIB_Analysis_Sheet.xlsx"

PROJECT_COLUMNS = [
    "project_id", "name", "sector", "keywords", "submitted_by", "group",
    "completeness_baseline", "completeness_risk", "completeness_control",
    "n_activities", "planned_duration_days", "bac", "has_resources",
    "real_duration", "real_cost", "duration_deviation", "cost_deviation",
    "sp", "ad", "la", "tf", "ri", "regularity", "excel_file",
]  # fmt: skip
ACTIVITY_COLUMNS = [
    "project_id", "activity_id", "name", "wbs", "is_summary", "predecessors", "successors",
    "baseline_start", "baseline_end", "duration_raw", "duration_days", "duration_hours",
    "resource_demand", "resource_cost", "fixed_cost", "variable_cost", "total_cost",
    "calendar_days",
]  # fmt: skip
TRACKING_COLUMNS = [
    "project_id", "period", "period_name", "is_final", "period_start", "status_date",
    "pv", "ev", "ac", "es", "sv", "spi", "cv", "cpi", "sv_t_raw", "spi_t", "p_factor",
]  # fmt: skip
ISSUE_COLUMNS = ["project_id", "table", "problem"]

# DSLIB sheet: our column -> header text in row 3 (header names verified in format_notes §4.1)
SUMMARY_TEXT = {
    "name": "Project name", "submitted_by": "Submitted by", "sector": "Sector",
    "keywords": "Keywords", "regularity": "Regularity",
}  # fmt: skip
SUMMARY_NUMBERS = {
    "n_activities": "# activities", "planned_duration_days": "PD (days)", "bac": "BAC",
    "real_duration": "Duration", "real_cost": "Cost", "duration_deviation": "Early/late",
    "cost_deviation": "Under/over budget", "sp": "SP", "ad": "AD", "la": "LA", "tf": "TF",
    "ri": "RI",
}  # fmt: skip
SUMMARY_COLOURS = {
    "completeness_baseline": "Baseline Schedule",
    "completeness_risk": "Risk Analysis",
    "completeness_control": "Project Control",
}
SUMMARY_REQUIRED = ["Code", "Resources", *SUMMARY_TEXT.values(), *SUMMARY_NUMBERS.values()]
SUMMARY_REQUIRED += list(SUMMARY_COLOURS.values())
SUMMARY_HEADER_ROW = 3
COLOURS = {"FF00FF00": "green", "FFFFFF00": "yellow", "FFFF8000": "orange", "FFFF8001": "orange"}

BASELINE_REQUIRED = ["ID", "Name", "Baseline Start", "Duration"]
BASELINE_MONEY = {
    "resource_cost": "Resource Cost", "fixed_cost": "Fixed Cost",
    "variable_cost": "Variable Cost", "total_cost": "Total Cost",
    "calendar_days": "Baseline duration (in calendar days)",
}  # fmt: skip
HEADER_ALIASES = {"Sussessors": "Successors"}  # typo in 2 real files

TRACKING_HEADER = {
    "period_name": "Name", "period_start": "Start Tracking Period", "status_date": "Status date",
    "pv": "Planned Value (PV)", "ev": "Earned Value (EV)", "ac": "Actual Cost (AC)",
    "es": "Earned Schedule (ES)", "sv": "Schedule Variance (SV)",
    "spi": "Schedule Performance Index (SPI)", "cv": "Cost Variance (CV)",
    "cpi": "Cost Performance Index (CPI)", "sv_t_raw": "Schedule Variance (SV(t))",
    "spi_t": "Schedule Performance Index (SPI(t))", "p_factor": "p-factor",
}  # fmt: skip
TRACKING_NUMBERS = ["pv", "ev", "ac", "sv", "spi", "cv", "cpi", "spi_t", "p_factor"]
TRACKING_DATES = ["period_start", "status_date", "es"]

MISSING_MARKERS = {"", "-", "N/A", "NA"}
_PROJECT_ID = re.compile(r"^C(\d{4})-(\d+)")
_TP_SHEET = re.compile(r"(Project Control - )?TP\d+")
_DURATION = re.compile(
    r"^(?:(?P<days>\d+(?:[.,]\d+)?)\s*(?:d|days?))?\s*(?:(?P<hours>\d+(?:[.,]\d+)?)\s*h)?$"
)


class GhentFormatError(ValueError):
    """A workbook does not have the layout the loader needs (e.g. a required column)."""


@dataclass
class GhentData:
    projects: pd.DataFrame
    activities: pd.DataFrame
    tracking: pd.DataFrame
    issues: pd.DataFrame


# --- small parsers --------------------------------------------------------------------------


def normalize_project_id(text: str) -> str:
    """`C2016-9 Railway Bridge.pdf` -> `C2016-09` (file names write IDs inconsistently)."""
    match = _PROJECT_ID.match(str(text).strip())
    if not match:
        raise ValueError(f"no project ID (like C2011-05) at the start of {text!r}")
    return f"C{match[1]}-{int(match[2]):02d}"


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value.strip() in MISSING_MARKERS


def parse_duration(value) -> tuple[float, float]:
    """`1d 2h` -> (1, 2); `58 days` -> (58, 0); `0` -> (0, 0). Unknown -> (nan, nan).

    Days and hours are kept apart: turning hours into days needs the project's calendar.
    """
    nan = (math.nan, math.nan)
    if value is None:
        return nan
    text = str(value).strip()
    if text in ("0", "0.0"):
        return (0.0, 0.0)
    match = _DURATION.match(text)
    if not text or not match:
        return nan
    days = float(match["days"].replace(",", ".")) if match["days"] else 0.0
    hours = float(match["hours"].replace(",", ".")) if match["hours"] else 0.0
    return (days, hours)


def parse_euro(value) -> float:
    """Numbers stay numbers; text like `€743 676` or `€ 464 186,97` becomes a float.

    The missing-value markers (`-`, `N/A`, empty) and unreadable text give NaN.
    """
    if isinstance(value, bool):
        return math.nan
    if isinstance(value, int | float):
        return float(value)
    if _is_missing(value):
        return math.nan
    text = re.sub(r"[€\s  ]", "", str(value))
    if "," in text and "." in text:  # 1.234,56
        text = text.replace(".", "")
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return math.nan


def _text(value) -> str | None:
    return None if _is_missing(value) else str(value).strip()


# --- loader ---------------------------------------------------------------------------------


class _Issues:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, project_id: str | None, table: str, problem: str) -> None:
        self.rows.append({"project_id": project_id, "table": table, "problem": problem})

    def number(self, value, project_id: str, table: str, what: str) -> float:
        """parse_euro + an issue when real text (not a missing marker) can't be read."""
        result = parse_euro(value)
        if math.isnan(result) and not _is_missing(value):
            self.add(project_id, table, f"{what} not a number: {value!r}")
        return result


def _header_map(row, file_name: str, sheet: str, required: list[str]) -> dict[str, int]:
    """Header text -> column index (first occurrence); raises if a required column is missing."""
    columns: dict[str, int] = {}
    for i, cell in enumerate(row):
        if cell is None:
            continue
        name = str(cell).strip()
        columns.setdefault(HEADER_ALIASES.get(name, name), i)
    for name in required:
        if name not in columns:
            raise GhentFormatError(f"{file_name}: sheet {sheet!r} is missing column {name!r}")
    return columns


def _find_header(rows: list[tuple], first: str) -> int | None:
    for i, row in enumerate(rows[:6]):
        if row and any(cell is not None and str(cell).strip() == first for cell in row):
            return i
    return None


def _cell(row: tuple, columns: dict[str, int], name: str):
    i = columns.get(name)
    return row[i] if i is not None and i < len(row) else None


def _wbs_parents(wbs_values: list[str | None]) -> set[str]:
    """Every WBS code that has children (`1.2` when `1.2.1` exists)."""
    parents = set()
    for wbs in wbs_values:
        if wbs:
            parts = wbs.split(".")
            parents.update(".".join(parts[:k]) for k in range(1, len(parts)))
    return parents


def _read_activities(rows, file_name: str, sheet: str, project_id: str, issues: _Issues):
    h = _find_header(rows, "ID")
    if h is None:
        raise GhentFormatError(f"{file_name}: sheet {sheet!r} has no header row with 'ID'")
    columns = _header_map(rows[h], file_name, sheet, BASELINE_REQUIRED)

    records, seen_project_row = [], False
    for row in rows[h + 1 :]:
        raw_id = _cell(row, columns, "ID")
        if _is_missing(raw_id):
            continue
        try:
            activity_id = int(float(str(raw_id).strip()))
        except ValueError:
            issues.add(project_id, "activities", f"activity_id not a number: {raw_id!r}")
            continue
        if activity_id == 0:  # the project itself, not an activity
            seen_project_row = True
            continue
        duration = _cell(row, columns, "Duration")
        days, hours = parse_duration(duration)
        if math.isnan(days) and not _is_missing(duration):
            issues.add(project_id, "activities", f"duration not understood: {duration!r}")
        wbs = _text(_cell(row, columns, "WBS"))
        record = {
            "project_id": project_id,
            "activity_id": activity_id,
            "name": _text(_cell(row, columns, "Name")),
            "wbs": wbs,
            "predecessors": _text(_cell(row, columns, "Predecessors")),
            "successors": _text(_cell(row, columns, "Successors")),
            "baseline_start": _cell(row, columns, "Baseline Start"),
            "baseline_end": _cell(row, columns, "Baseline End"),
            "duration_raw": None if duration is None else str(duration).strip(),
            "duration_days": days,
            "duration_hours": hours,
            "resource_demand": _text(_cell(row, columns, "Resource Demand")),
        }
        for ours, theirs in BASELINE_MONEY.items():
            record[ours] = issues.number(
                _cell(row, columns, theirs), project_id, "activities", theirs
            )
        records.append(record)

    if not seen_project_row:
        issues.add(project_id, "activities", "no ID 0 row")
    parents = _wbs_parents([r["wbs"] for r in records])
    for record in records:
        record["is_summary"] = record["wbs"] in parents
    counts = pd.Series([r["activity_id"] for r in records]).value_counts()
    for activity_id in sorted(counts[counts > 1].index):
        issues.add(project_id, "activities", f"duplicate activity_id {activity_id}")
    return records


def _read_tracking(rows, file_name: str, project_id: str, issues: _Issues) -> list[dict]:
    h = _find_header(rows, "Name")
    if h is None:
        return []
    data_rows = [r for r in rows[h + 1 :] if r and not _is_missing(r[0])]
    if not data_rows:
        return []
    columns = _header_map(rows[h], file_name, "Tracking Overview", list(TRACKING_HEADER.values()))
    records = []
    for period, row in enumerate(data_rows, start=1):
        record = {"project_id": project_id, "period": period}
        for ours, theirs in TRACKING_HEADER.items():
            record[ours] = _cell(row, columns, theirs)
        for name in TRACKING_NUMBERS:
            record[name] = issues.number(record[name], project_id, "tracking", name)
        record["period_name"] = str(record["period_name"]).strip()
        record["is_final"] = record["period_name"] == "Actual Schedule"
        sv_t = record["sv_t_raw"]
        record["sv_t_raw"] = None if sv_t is None else str(sv_t).strip()
        records.append(record)
    return records


def _read_workbook(path: Path, issues: _Issues) -> tuple[str, str, list[dict], list[dict]]:
    """One project workbook -> (project_id, group, activity records, tracking records)."""
    project_id = normalize_project_id(path.name)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = {ws.title.strip(): ws for ws in wb.worksheets}
        baseline = next((n for n in sheets if n.startswith("Baseline Schedule")), None)
        if baseline is None:
            raise GhentFormatError(f"{path.name}: no 'Baseline Schedule' sheet")
        rows = list(sheets[baseline].iter_rows(values_only=True))
        activities = _read_activities(rows, path.name, baseline, project_id, issues)
        tracking = []
        if "Tracking Overview" in sheets:
            rows = list(sheets["Tracking Overview"].iter_rows(values_only=True))
            tracking = _read_tracking(rows, path.name, project_id, issues)
        has_tp_sheets = any(_TP_SHEET.fullmatch(n) for n in sheets)
    finally:
        wb.close()
    group = "A" if tracking else ("B" if has_tp_sheets else "C")
    return project_id, group, activities, tracking


def _sector(value) -> str | None:
    """First word as written, the rest lower case: `Construction (Civil)` -> `(civil)`."""
    text = _text(value)
    if text is None:
        return None
    first, _, rest = text.partition(" ")
    return f"{first} {rest.lower()}" if rest else first


def _read_projects(path: Path, issues: _Issues) -> list[dict]:
    wb = openpyxl.load_workbook(path, data_only=True)  # not read-only: fill colours are needed
    try:
        if "DSLIB" not in wb.sheetnames:
            raise GhentFormatError(f"{path.name}: no 'DSLIB' sheet")
        ws = wb["DSLIB"]
        header = [c.value for c in ws[SUMMARY_HEADER_ROW]]
        columns = _header_map(header, path.name, "DSLIB", SUMMARY_REQUIRED)
        records = []
        for row in ws.iter_rows(min_row=SUMMARY_HEADER_ROW + 1):
            code = row[columns["Code"]].value
            if code is None or not _PROJECT_ID.match(str(code).strip()):
                continue  # empty rows and the summary statistics below the projects
            pid = normalize_project_id(code)
            record = {"project_id": pid}
            for ours, theirs in SUMMARY_TEXT.items():
                record[ours] = _text(row[columns[theirs]].value)
            record["sector"] = _sector(row[columns["Sector"]].value)
            if record["regularity"]:
                record["regularity"] = record["regularity"].lower()
            for ours, theirs in SUMMARY_NUMBERS.items():
                record[ours] = issues.number(row[columns[theirs]].value, pid, "projects", theirs)
            for ours, theirs in SUMMARY_COLOURS.items():
                fill = row[columns[theirs]].fill
                rgb = fill.fgColor.rgb if fill is not None and fill.fill_type else None
                record[ours] = COLOURS.get(rgb) if isinstance(rgb, str) else None
                if isinstance(rgb, str) and rgb not in COLOURS:
                    issues.add(pid, "projects", f"{theirs}: unknown colour {rgb}")
            resources = _text(row[columns["Resources"]].value)
            record["has_resources"] = {"Y": True, "N": False}.get(resources)
            if resources is not None and resources not in ("Y", "N"):
                issues.add(pid, "projects", f"Resources not Y/N: {resources!r}")
            bac = record["bac"]
            if math.isnan(bac):
                issues.add(pid, "projects", "BAC missing")
            elif bac <= 0:
                issues.add(pid, "projects", f"BAC not positive: {bac}")
            records.append(record)
        return records
    finally:
        wb.close()


def load_ghent(path: Path | str = DEFAULT_DIR) -> GhentData:
    """Read a DSLIB folder (the one holding `DSLIB_Analysis_Sheet.xlsx` and `Excel/`)."""
    root = Path(path)
    analysis, excel_dir = root / ANALYSIS_FILE, root / "Excel"
    for needed in (analysis, excel_dir):
        if not needed.exists():
            raise FileNotFoundError(f"not found: {needed}")

    issues = _Issues()
    projects = _read_projects(analysis, issues)
    activities, tracking, workbooks = [], [], {}
    for file in sorted(excel_dir.glob("*.xlsx")):
        if file.name.startswith("~$"):  # Excel lock file
            continue
        project_id, group, acts, track = _read_workbook(file, issues)
        if project_id in workbooks:
            issues.add(project_id, "projects", f"two workbooks: {file.name}")
            continue
        workbooks[project_id] = (file.name, group)
        activities += acts
        tracking += track

    for record in projects:
        file_name, group = workbooks.get(record["project_id"], (None, None))
        record["excel_file"], record["group"] = file_name, group
        if file_name is None:
            issues.add(record["project_id"], "projects", "no workbook in Excel/")
    in_summary = {r["project_id"] for r in projects}
    for project_id in sorted(set(workbooks) - in_summary):
        issues.add(project_id, "projects", "workbook not in the analysis sheet")

    return GhentData(
        projects=_projects_frame(projects),
        activities=_activities_frame(activities),
        tracking=_tracking_frame(tracking),
        issues=pd.DataFrame(issues.rows, columns=ISSUE_COLUMNS),
    )


# --- DataFrame types ------------------------------------------------------------------------


def _projects_frame(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records, columns=PROJECT_COLUMNS)
    df = df.astype({c: float for c in SUMMARY_NUMBERS if c != "n_activities"})
    df["n_activities"] = df["n_activities"].astype("Int64")
    # Label columns: missing = None. pandas 3 would store them as `str` with NaN for missing.
    labels = [c for c in PROJECT_COLUMNS if c not in SUMMARY_NUMBERS and c != "project_id"]
    df[labels] = df[labels].astype(object).where(df[labels].notna(), None)
    return df.sort_values("project_id", ignore_index=True)


def _activities_frame(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records, columns=ACTIVITY_COLUMNS)
    df["activity_id"] = df["activity_id"].astype("int64")
    df["is_summary"] = df["is_summary"].astype(bool)
    for col in ("baseline_start", "baseline_end"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df.astype({c: float for c in [*BASELINE_MONEY, "duration_days", "duration_hours"]})


def _tracking_frame(records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records, columns=TRACKING_COLUMNS)
    df["period"] = df["period"].astype("int64")
    df["is_final"] = df["is_final"].astype(bool)
    for col in TRACKING_DATES:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df.astype({c: float for c in TRACKING_NUMBERS})


# --- command line ---------------------------------------------------------------------------


def summary(data: GhentData) -> str:
    p = data.projects
    a, t = data.activities, data.tracking
    groups = p["group"].value_counts().sort_index().to_dict()
    lines = [
        f"projects:   {len(p)}  (groups: {groups})",
        f"activities: {len(a)}  ({int(a['is_summary'].sum())} WBS summary rows)",
        f"tracking:   {len(t)} periods in {t['project_id'].nunique()} projects",
        f"issues:     {len(data.issues)}",
    ]
    if len(data.issues):
        kinds = data.issues["problem"].str.replace(r":.*| \d+$", "", regex=True).value_counts()
        lines += [f"  {n:5d}  {kind}" for kind, n in kinds.items()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Load the Ghent DSLIB data and print a summary.")
    parser.add_argument("path", nargs="?", default=DEFAULT_DIR, type=Path)
    print(summary(load_ghent(parser.parse_args(argv).path)))


if __name__ == "__main__":
    main()
