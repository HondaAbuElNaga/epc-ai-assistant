"""Profile functions for the dataset notebooks. Spec: specs/2026-10-16-profiling-notebooks/spec.md.

All tests build tiny fake files in a temporary folder; CI has no real data.
"""

from pathlib import Path

import matplotlib.image
import numpy as np
import pandas as pd
import pymupdf
import pytest

from src.datasets import profiling

# --- missing values -------------------------------------------------------------------------


def test_missing_table_counts_and_percent_per_column():
    df = pd.DataFrame({"a": [1, None, 3, None], "b": ["x", "y", None, "z"], "c": [1, 2, 3, 4]})
    table = profiling.missing_table(df)
    assert list(table.columns) == ["column", "missing", "missing_pct"]
    assert table["column"].tolist() == ["a", "b", "c"]  # same order as the DataFrame
    assert table["missing"].tolist() == [2, 1, 0]
    assert table["missing_pct"].tolist() == [50.0, 25.0, 0.0]


def test_missing_table_of_empty_frame_has_zero_percent():
    table = profiling.missing_table(pd.DataFrame({"a": []}))
    assert table["missing"].tolist() == [0]
    assert table["missing_pct"].tolist() == [0.0]


# --- PDFs -----------------------------------------------------------------------------------


def _make_pdf(path: Path, page_texts: list[str]) -> None:
    """A PDF with one page per text; an empty string makes a page without a text layer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_pdf_stats_counts_pages_text_and_empty_pages(tmp_path):
    pdf = tmp_path / "UFGS_01_11_00.pdf"
    _make_pdf(pdf, ["SECTION 01 11 00", "", "PART 1 GENERAL"])
    stats = profiling.pdf_stats(pdf)
    assert stats["pages"] == 3
    assert stats["empty_pages"] == 1
    assert stats["text_chars"] == len("SECTION 01 11 00") + len("PART 1 GENERAL")


def test_ufgs_pdf_stats_one_row_per_pdf_with_division(tmp_path):
    _make_pdf(tmp_path / "01" / "UFGS_01_11_00.pdf", ["SUMMARY OF WORK"])
    _make_pdf(tmp_path / "03" / "UFGS_03_30_00.pdf", ["CAST-IN-PLACE CONCRETE", ""])
    (tmp_path / "manifest.json").write_text("{}")  # not a PDF: ignored
    table = profiling.ufgs_pdf_stats(tmp_path)
    assert list(table.columns) == [
        "division", "file", "bytes", "pages", "text_chars", "empty_pages",
    ]  # fmt: skip
    assert table["file"].tolist() == ["UFGS_01_11_00.pdf", "UFGS_03_30_00.pdf"]
    assert table["division"].tolist() == ["01", "03"]
    assert table["pages"].tolist() == [1, 2]
    assert table["empty_pages"].tolist() == [0, 1]
    assert (table["bytes"] > 0).all()


def test_ufgs_pdf_stats_of_empty_folder_has_the_columns(tmp_path):
    table = profiling.ufgs_pdf_stats(tmp_path)
    assert table.empty
    assert "text_chars" in table.columns


def test_first_lines_returns_non_empty_lines_of_first_page(tmp_path):
    pdf = tmp_path / "a.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "SECTION 01 11 00")
    page.insert_text((72, 120), "SUMMARY OF WORK")
    page.insert_text((72, 168), "PART 1 GENERAL")
    doc.save(pdf)
    doc.close()
    assert profiling.first_lines(pdf, 2) == ["SECTION 01 11 00", "SUMMARY OF WORK"]


# --- images ---------------------------------------------------------------------------------


@pytest.mark.parametrize("suffix", [".png", ".jpg"])
def test_image_size_reads_width_and_height_from_header(tmp_path, suffix):
    path = tmp_path / f"drawing{suffix}"
    matplotlib.image.imsave(path, np.zeros((30, 50, 3), dtype=np.uint8))  # 50 wide, 30 high
    assert profiling.image_size(path) == (50, 30)


def test_image_size_rejects_other_files(tmp_path):
    path = tmp_path / "not_an_image.png"
    path.write_bytes(b"GIF89a....")
    with pytest.raises(ValueError, match="not a PNG or JPEG"):
        profiling.image_size(path)


def test_image_size_rejects_jpeg_without_size_marker(tmp_path):
    path = tmp_path / "broken.jpg"
    path.write_bytes(b"\xff\xd8\xff\xd9")  # start of image, then end of image
    with pytest.raises(ValueError, match="no size"):
        profiling.image_size(path)


def test_image_size_rejects_truncated_jpeg(tmp_path):
    path = tmp_path / "cut.jpg"
    path.write_bytes(b"\xff\xd8\xff\xe0\x00")  # an APP0 marker, then the file ends
    with pytest.raises(ValueError, match="cut off"):
        profiling.image_size(path)


def test_image_sizes_one_row_per_image(tmp_path):
    matplotlib.image.imsave(tmp_path / "1.png", np.zeros((10, 20, 3), dtype=np.uint8))
    matplotlib.image.imsave(tmp_path / "2.jpg", np.zeros((40, 30, 3), dtype=np.uint8))
    (tmp_path / "1.graphml").write_text("<graphml/>")  # not an image: ignored
    table = profiling.image_sizes(tmp_path)
    assert table.to_dict("records") == [
        {"file": "1.png", "width": 20, "height": 10},
        {"file": "2.jpg", "width": 30, "height": 40},
    ]


# --- GraphML --------------------------------------------------------------------------------

# Same layout as PID2Graph: box keys exist twice (double and long), only one set is used.
GRAPHML = """<?xml version='1.0' encoding='utf-8'?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d9" for="edge" attr.name="edge_label" attr.type="string" />
  <key id="d8" for="node" attr.name="ymax" attr.type="long" />
  <key id="d7" for="node" attr.name="xmax" attr.type="long" />
  <key id="d6" for="node" attr.name="ymin" attr.type="long" />
  <key id="d5" for="node" attr.name="xmin" attr.type="long" />
  <key id="d4" for="node" attr.name="ymax" attr.type="double" />
  <key id="d3" for="node" attr.name="ymin" attr.type="double" />
  <key id="d2" for="node" attr.name="xmax" attr.type="double" />
  <key id="d1" for="node" attr.name="xmin" attr.type="double" />
  <key id="d0" for="node" attr.name="label" attr.type="string" />
  <graph edgedefault="undirected">
    <node id="valve1">
      <data key="d0">valve</data>
      <data key="d1">10.5</data><data key="d2">30.5</data>
      <data key="d3">100</data><data key="d4">140</data>
    </node>
    <node id="pump1">
      <data key="d0">pump</data>
      <data key="d5">0</data><data key="d7">50</data>
      <data key="d6">0</data><data key="d8">25</data>
    </node>
    <node id="crossing1" />
    <edge source="valve1" target="pump1"><data key="d9">solid</data></edge>
    <edge source="pump1" target="crossing1" />
  </graph>
</graphml>
"""


@pytest.fixture
def graphml(tmp_path: Path) -> Path:
    path = tmp_path / "0.graphml"
    path.write_text(GRAPHML, encoding="utf-8")
    return path


def test_read_graphml_nodes_with_box_and_label(graphml):
    nodes, _ = profiling.read_graphml(graphml)
    assert list(nodes.columns) == ["id", "label", "xmin", "ymin", "xmax", "ymax"]
    assert nodes["id"].tolist() == ["valve1", "pump1", "crossing1"]
    assert nodes["label"].tolist()[:2] == ["valve", "pump"]
    assert nodes.loc[0, ["xmin", "ymin", "xmax", "ymax"]].tolist() == [10.5, 100.0, 30.5, 140.0]
    assert nodes.loc[1, ["xmin", "ymin", "xmax", "ymax"]].tolist() == [0.0, 0.0, 50.0, 25.0]
    assert pd.isna(nodes.loc[2, "label"]) and pd.isna(nodes.loc[2, "xmin"])


def test_read_graphml_blank_box_value_counts_as_missing(tmp_path):
    path = tmp_path / "blank.graphml"
    path.write_text(GRAPHML.replace('<data key="d1">10.5</data>', '<data key="d1"> </data>'))
    nodes, _ = profiling.read_graphml(path)
    assert pd.isna(nodes.loc[0, "xmin"]) and nodes.loc[0, "xmax"] == 30.5


def test_read_graphml_edges_with_label(graphml):
    _, edges = profiling.read_graphml(graphml)
    assert list(edges.columns) == ["source", "target", "label"]
    assert edges[["source", "target"]].values.tolist() == [
        ["valve1", "pump1"],
        ["pump1", "crossing1"],
    ]
    assert edges.loc[0, "label"] == "solid" and pd.isna(edges.loc[1, "label"])


def test_graphml_stats_one_row_per_drawing(graphml, tmp_path):
    empty = tmp_path / "1.graphml"
    empty.write_text(
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"><graph/></graphml>',
        encoding="utf-8",
    )
    table = profiling.graphml_stats(tmp_path)
    assert table.to_dict("records") == [
        {"file": "0.graphml", "nodes": 3, "edges": 2, "no_box": 1, "no_label": 1, "labels": 2},
        {"file": "1.graphml", "nodes": 0, "edges": 0, "no_box": 0, "no_label": 0, "labels": 0},
    ]


def test_graphml_boxes_width_and_height_per_node(graphml, tmp_path):
    table = profiling.graphml_boxes(tmp_path)
    assert list(table.columns) == ["file", "label", "width", "height"]
    assert table.to_dict("records") == [
        {"file": "0.graphml", "label": "valve", "width": 20.0, "height": 40.0},
        {"file": "0.graphml", "label": "pump", "width": 50.0, "height": 25.0},
    ]  # the node without a box is left out


# --- .npy headers ---------------------------------------------------------------------------


def test_npy_shape_reads_header_of_plain_array(tmp_path):
    path = tmp_path / "0_lines2.npy"
    np.save(path, np.zeros((68, 5), dtype=np.int64))
    assert profiling.npy_shape(path) == ((68, 5), "int64", False)


def test_npy_shape_does_not_unpickle_object_arrays(tmp_path, monkeypatch):
    path = tmp_path / "0_symbols.npy"
    np.save(path, np.array([["a", [1, 2]], ["b", [3]]], dtype=object), allow_pickle=True)

    def _no_pickle(*args, **kwargs):
        raise AssertionError("pickle must not be used")

    monkeypatch.setattr("pickle.load", _no_pickle)
    monkeypatch.setattr("pickle.loads", _no_pickle)
    assert profiling.npy_shape(path) == ((2, 2), "object", True)


def test_npy_shape_rejects_other_files(tmp_path):
    path = tmp_path / "x.npy"
    path.write_bytes(b"not numpy")
    with pytest.raises(ValueError):
        profiling.npy_shape(path)


def test_npy_shapes_one_row_per_file_with_drawing_and_kind(tmp_path):
    for drawing in ("0", "1"):
        (tmp_path / drawing).mkdir()
        np.save(tmp_path / drawing / f"{drawing}_lines2.npy", np.zeros((3, 5), dtype=np.int64))
        np.save(tmp_path / drawing / f"{drawing}_KeyValue.npy", np.array([["Sheet", "1"]]))
    table = profiling.npy_shapes(tmp_path)
    assert list(table.columns) == ["drawing", "kind", "rows", "cols", "dtype", "needs_pickle"]
    assert table[["drawing", "kind", "rows", "cols"]].values.tolist() == [
        [0, "KeyValue", 1, 2],
        [0, "lines2", 3, 5],
        [1, "KeyValue", 1, 2],
        [1, "lines2", 3, 5],
    ]
    assert not table["needs_pickle"].any()
