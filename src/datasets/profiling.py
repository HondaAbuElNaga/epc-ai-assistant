"""Small profile functions for the dataset notebooks (`notebooks/00_profile_<dataset>.ipynb`).

Spec: specs/2026-10-16-profiling-notebooks/spec.md

Every function takes a file or folder path and returns plain values or a pandas DataFrame, so the
notebooks only call and show them, and tests can use a tiny fake dataset.

Memory-light on purpose (the real drawings are about 7,168 x 4,561 px):
- image sizes come from the PNG/JPEG **header**; the image is never decoded;
- PDFs are opened one at a time and closed again;
- `.npy` shapes come from the **header**; object arrays are never unpickled (pickle can run code).
"""

import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import pymupdf
from numpy.lib import format as npy_format

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
# JPEG "start of frame" markers hold the size; C4, C8 and CC have other meanings
JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"
BOX = ["xmin", "ymin", "xmax", "ymax"]

# --- missing values -------------------------------------------------------------------------


def missing_table(df: pd.DataFrame) -> pd.DataFrame:
    """Missing count and percent per column, in the DataFrame's column order."""
    missing = df.isna().sum()
    pct = (missing / len(df) * 100).round(2) if len(df) else missing * 0.0
    return pd.DataFrame(
        {"column": df.columns, "missing": missing.to_numpy(), "missing_pct": pct.to_numpy()}
    )


# --- PDFs (UFGS) ----------------------------------------------------------------------------


def pdf_stats(path: Path) -> dict:
    """Pages, characters of text and pages without any text (would need OCR) of one PDF."""
    with pymupdf.open(path) as doc:
        texts = [page.get_text().strip() for page in doc]
    return {
        "pages": len(texts),
        "text_chars": sum(len(t) for t in texts),
        "empty_pages": sum(1 for t in texts if not t),
    }


def ufgs_pdf_stats(folder: Path) -> pd.DataFrame:
    """One row per `<division>/*.pdf` under `folder` (the UFGS layout)."""
    rows = [
        {"division": pdf.parent.name, "file": pdf.name, "bytes": pdf.stat().st_size}
        | pdf_stats(pdf)
        for pdf in sorted(Path(folder).glob("*/*.pdf"))
    ]
    columns = ["division", "file", "bytes", "pages", "text_chars", "empty_pages"]
    return pd.DataFrame(rows, columns=columns)


def first_lines(path: Path, n: int = 5) -> list[str]:
    """The first `n` non-empty lines of text on page 1 (a short sample)."""
    with pymupdf.open(path) as doc:
        text = doc[0].get_text() if len(doc) else ""
    return [line.strip() for line in text.splitlines() if line.strip()][:n]


# --- images ---------------------------------------------------------------------------------


def _read(f, n: int) -> bytes:
    data = f.read(n)
    if len(data) < n:
        raise ValueError("JPEG is cut off (truncated file)")
    return data


def _jpeg_size(f) -> tuple[int, int]:
    f.seek(2)  # after the start-of-image marker FF D8
    while True:
        byte = f.read(1)
        if not byte:
            raise ValueError("JPEG has no size (no start-of-frame marker)")
        if byte != b"\xff":
            continue
        marker = f.read(1)
        while marker == b"\xff":  # fill bytes
            marker = f.read(1)
        if not marker:
            raise ValueError("JPEG has no size (no start-of-frame marker)")
        code = marker[0]
        if code == 0xD9:  # end of image
            raise ValueError("JPEG has no size (no start-of-frame marker)")
        if code in (0x01, *range(0xD0, 0xD9)):  # markers without a length
            continue
        (length,) = struct.unpack(">H", _read(f, 2))
        if code in JPEG_SOF:
            _precision, height, width = struct.unpack(">BHH", _read(f, 5))
            return width, height
        f.seek(length - 2, 1)


def image_size(path: Path) -> tuple[int, int]:
    """(width, height) of a PNG or JPEG, read from the file header only."""
    with open(path, "rb") as f:
        head = f.read(24)
        if head.startswith(PNG_SIGNATURE) and head[12:16] == b"IHDR":
            width, height = struct.unpack(">II", head[16:24])
            return width, height
        if head.startswith(b"\xff\xd8"):
            return _jpeg_size(f)
    raise ValueError(f"not a PNG or JPEG: {path}")


def image_sizes(folder: Path) -> pd.DataFrame:
    """One row per PNG/JPEG file directly in `folder`."""
    files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    rows = [(p.name, *image_size(p)) for p in files]
    return pd.DataFrame(rows, columns=["file", "width", "height"])


# --- GraphML (PID2Graph) --------------------------------------------------------------------


def read_graphml(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Nodes (id, label, box) and edges (source, target, label) of one `.graphml` drawing.

    PID2Graph declares the box keys twice (as double and as long); keys are matched by their
    `attr.name`, so either set works.
    """
    root = ET.parse(path).getroot()
    names = {key.get("id"): key.get("attr.name") for key in root.iter(f"{GRAPHML_NS}key")}

    def values(element) -> dict:
        return {names.get(d.get("key")): d.text for d in element.findall(f"{GRAPHML_NS}data")}

    nodes, edges = [], []
    for node in root.iter(f"{GRAPHML_NS}node"):
        data = values(node)
        box = {k: float(data[k]) if (data.get(k) or "").strip() else None for k in BOX}
        nodes.append({"id": node.get("id"), "label": data.get("label"), **box})
    for edge in root.iter(f"{GRAPHML_NS}edge"):
        label = values(edge).get("edge_label")
        edges.append({"source": edge.get("source"), "target": edge.get("target"), "label": label})
    nodes_df = pd.DataFrame(nodes, columns=["id", "label", *BOX]).astype({k: float for k in BOX})
    return nodes_df, pd.DataFrame(edges, columns=["source", "target", "label"])


def graphml_stats(folder: Path) -> pd.DataFrame:
    """One row per `.graphml` in `folder`: nodes, edges, nodes without box or label, labels."""
    rows = []
    for path in sorted(Path(folder).glob("*.graphml")):
        nodes, edges = read_graphml(path)
        rows.append(
            {
                "file": path.name,
                "nodes": len(nodes),
                "edges": len(edges),
                "no_box": int(nodes[BOX].isna().any(axis=1).sum()),
                "no_label": int(nodes["label"].isna().sum()),
                "labels": int(nodes["label"].nunique()),
            }
        )
    return pd.DataFrame(rows, columns=["file", "nodes", "edges", "no_box", "no_label", "labels"])


def graphml_boxes(folder: Path) -> pd.DataFrame:
    """One row per node with a full box: its label and box width and height (in pixels)."""
    frames = []
    for path in sorted(Path(folder).glob("*.graphml")):
        nodes, _ = read_graphml(path)
        nodes = nodes.dropna(subset=BOX)
        frames.append(
            pd.DataFrame(
                {
                    "file": path.name,
                    "label": nodes["label"],
                    "width": nodes["xmax"] - nodes["xmin"],
                    "height": nodes["ymax"] - nodes["ymin"],
                }
            )
        )
    if not frames:
        return pd.DataFrame(columns=["file", "label", "width", "height"])
    return pd.concat(frames, ignore_index=True)


# --- .npy headers (Dataset-P&ID) ------------------------------------------------------------


def npy_shape(path: Path) -> tuple[tuple[int, ...], str, bool]:
    """(shape, dtype, needs_pickle) from the `.npy` header; the array itself is never read."""
    with open(path, "rb") as f:
        version = npy_format.read_magic(f)  # ValueError if not a .npy file
        if version == (1, 0):
            shape, _fortran, dtype = npy_format.read_array_header_1_0(f)
        elif version == (2, 0):
            shape, _fortran, dtype = npy_format.read_array_header_2_0(f)
        else:
            raise ValueError(f"unsupported .npy version {version}: {path}")
    return tuple(shape), str(dtype), bool(dtype.hasobject)


def npy_shapes(folder: Path) -> pd.DataFrame:
    """One row per `<drawing>/<drawing>_<kind>.npy` under `folder` (the Dataset-P&ID layout)."""
    rows = []
    for path in Path(folder).glob("*/*.npy"):
        shape, dtype, needs_pickle = npy_shape(path)
        rows.append(
            {
                "drawing": int(path.parent.name),
                "kind": path.stem.split("_", 1)[1],
                "rows": shape[0] if shape else 1,
                "cols": shape[1] if len(shape) > 1 else None,
                "dtype": dtype,
                "needs_pickle": needs_pickle,
            }
        )
    columns = ["drawing", "kind", "rows", "cols", "dtype", "needs_pickle"]
    table = pd.DataFrame(rows, columns=columns)
    return table.sort_values(["drawing", "kind"], ignore_index=True)
