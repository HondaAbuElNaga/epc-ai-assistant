# Format notes: PID2Graph + Dataset-P&ID (task 9)

Inspected 2026-10-16 inside the `dev` container, on the files downloaded on 2026-10-14/15 (see
`tasks.md` 6–8). Every number below comes from reading the files with the commands described in
each section, using only the standard library and NumPy. Nothing is taken from the papers unless
it says so. Inferences are marked **(inference)**.

## 0. Plain-language guide (read this first)

### The big idea
Each dataset is a set of **P&ID drawings**, each with an **"answer key"**:
- the **drawing** is a picture (`.png` / `.jpg`);
- the **answer key** says *"there's a valve here, a pump there, and this line connects them"*.

In Phase 7 we show the computer the drawings **together with** their answer keys, so it learns to
find the symbols by itself. Every folder below holds either **pictures** or **answer keys**.

### Folder 1: `data/raw/pid/pid2graph/`, the PID2Graph dataset

```
pid2graph/
├── PID2Graph.zip          ← the original 9.3 GB download (kept as a backup)
├── manifest.json          ← our receipt: what we downloaded, when, size, checksum
└── PID2Graph/Complete/    ← the unpacked drawings
    ├── Dataset PID/            500 drawings (computer-made)
    ├── PID2Graph OPEN100/       12 drawings (REAL, from a nuclear plant design)
    └── PID2Graph Synthetic/    250 drawings (computer-made)
```

Each of the three folders holds **pairs** of files with the same number:

| File | What it is |
|---|---|
| `0.png` | **The picture** of drawing 0 |
| `0.graphml` | **The answer key** of drawing 0 (a text file) |

The answer key lists two kinds of things:

**1. Things on the drawing, each with a box around it**, e.g.
`valve at box (2435, 932) → (2539, 1009)`. The numbers are **pixel positions** in the picture:
top-left corner → bottom-right corner.

| Name | Meaning |
|---|---|
| `valve`, `pump`, `tank`, `instrumentation`, `arrow`, `inlet/outlet`, `general` | **Real symbols** (`general` = "other symbol") |
| `connector` | A tiny 8×8 dot where a pipe touches a symbol |
| `crossing` | A tiny 8×8 dot where two pipes cross |
| `background` | The empty border/frame of the drawing; ignore it |

**2. Lines between them**, e.g. `valve1 ── solid ── connector5`: a pipe (`solid`) or a signal
line (`non-solid`, dashed) connecting two things.

In short: the `.graphml` says *which symbols are where, and which are connected by pipes*.

### Folder 2: `data/raw/pid/dataset_pid/`, the original Dataset-P&ID

```
dataset_pid/
├── manifest.json, drive_listing.json   ← our receipts
├── image_2.tar.gz, mask.tar.gz         ← the original packed downloads (backup)
├── image_2/image_2/
│     0.jpg … 499.jpg                    ← THE PICTURES (500 drawings)
├── mask/mask/
│     0_mask.png … 499_mask.png          ← black-and-white helper images (not studied yet)
└── 0/  1/  2/ … 499/                    ← THE ANSWER KEYS, one folder per drawing
```

Each numbered folder (e.g. `0/`) has **7 answer-key files for that drawing**:

| File | What it holds (drawing 0 example) | Opened? |
|---|---|---|
| `0_symbols.npy` | **Symbols** with boxes: `symbol_1` at (1669, 767)–(1702, 829), type `21` | 🔒 not yet |
| `0_words.npy` | **Text** on the drawing and where it is: `"SDL"`, `"101"` | 🔒 not yet |
| `0_lines.npy` | **Pipes**: start/end point, pipe number (`5"-EK-2648`), solid or dashed | 🔒 not yet |
| `0_linker.npy` | **Which text and pipe belong to which symbol**: `symbol_11` ↔ `word_1,word_2` + `line_75` | 🔒 not yet |
| `0_lines2.npy` | Lines of the drawing's **frame and table** (inference) | ✅ yes |
| `0_KeyValue.npy` | The **title block**: `ORGANIZATION = P-0`, `CONTRACTOR PROJECT NO. = AI-2148` | ✅ yes |
| `0_Table.npy` | The **revision table**: `ISSUE A, 15/07/22, ISSUE CONSTR. REV.1` | ✅ yes |

🔒 = these 4 files use "pickle", a format that can run code when opened. They have **not been
opened**, for safety; only their text was read (§4.2). Opening them is the owner's decision for
Phase 7.

### Why the two datasets look like they hold "the same" drawings
PID2Graph's `Dataset PID` folder is a **converted copy** of Dataset-P&ID, but:
- it is **simplified**: 32 symbol types became 7, and the text and tables were removed;
- it has **not been confirmed** that drawing `0` in one is drawing `0` in the other (§6).

So: **use each dataset's pictures only with its own answer keys.**

### One line per folder

| Folder | One line |
|---|---|
| `pid2graph/.../Dataset PID` | 500 computer-made drawings + simple answer keys (7 symbol types + pipes) |
| `pid2graph/.../PID2Graph OPEN100` | **12 real drawings** + answer keys; the most valuable for testing |
| `pid2graph/.../PID2Graph Synthetic` | 250 computer-made drawings + answer keys |
| `dataset_pid/image_2` | 500 drawings (pictures) |
| `dataset_pid/0 … 499` | detailed answer keys for those 500 (32 symbol types, text, pipes, tables) |
| `dataset_pid/mask` | 500 helper images; purpose not checked yet |

To **see** one: open `data/raw/pid/pid2graph/PID2Graph/Complete/PID2Graph OPEN100/0.png` (a real
P&ID) and its answer key `0.graphml` in a text editor.

The sections below are the technical details behind this guide.

## 1. Where the files are

```
data/raw/pid/                                   (git-ignored)
├── pid2graph/
│   ├── PID2Graph.zip                           9,303,633,645 B, MD5 90f782220de97e7e249d2595c49ddc1c
│   ├── manifest.json
│   └── PID2Graph/Complete/
│       ├── Dataset PID/          0…499 .png + .graphml
│       ├── PID2Graph OPEN100/    0…11  .png + .graphml   ← the only real drawings
│       └── PID2Graph Synthetic/  0…249 .jpg + .graphml
└── dataset_pid/
    ├── drive_listing.json, manifest.json
    ├── image_2.tar.gz, mask.tar.gz
    ├── 0/ … 499/                 7 .npy each: KeyValue, Table, lines, lines2, linker, symbols, words
    ├── image_2/image_2/<n>.jpg   500 drawings
    └── mask/mask/<n>_mask.png    500 masks
```

## 2. PID2Graph images

Sizes read from the PNG `IHDR` header and the JPEG `SOF` marker (width × height, px).

| Set | Files | Format | Sizes |
|---|---|---|---|
| Dataset PID | 500 | PNG, 8-bit RGB (colour type 2) | 7168 × 4561 (300), 7168 × 4562 (200) |
| OPEN100 | 12 | PNG | 12 different sizes: width 1994–3342, height 1330–2222 (e.g. 2604 × 1744) |
| Synthetic | 250 | JPEG | all 7000 × 4500 |

The real OPEN100 drawings are **about 2–3.5× narrower** than the synthetic ones (1,994–3,342 vs
7,000–7,168 px), and their symbols are smaller too (§3.4). This matters for tiling in Phase 7.

## 3. PID2Graph `.graphml` files

Parsed with `xml.etree` (namespace `http://graphml.graphdrawing.org/xmlns`).

### 3.1 Structure
- One `<graph edgedefault="undirected">` per file (all 762 files). Edges have no direction.
- **Nodes** = symbols *and* helper points. Each node has `label`, `xmin`, `ymin`, `xmax`,
  `ymax` (pixels, in the image of the same number). Node IDs are `<label><n>`, e.g.
  `crossing1`, `general1`.
- **Edges** = line pieces between two nodes (`source`, `target`) with one attribute,
  `edge_label`.

Example (Synthetic `0.graphml`):
```
node general1  label=general  xmin=4374.0 ymin=3649.0 xmax=4529.0 ymax=3812.0
edge general1 → connector88   edge_label=solid
```

### 3.2 Trap: the key IDs are not fixed
Every file declares 10 `<key>`s: `label`, `edge_label`, and `xmin`/`ymin`/`xmax`/`ymax`
**twice**, once as `long` and once as `double`. Two consequences:
- **The `dN` IDs mean different things in different files.** `d1` is `xmin (long)` in Dataset
  PID `0.graphml` but `xmin (double)` in OPEN100 `0.graphml`, and `d3` is `xmax` in one and
  `ymin` in another. A reader must map IDs to names **per file**, using `attr.name`.
- **A node uses either the `long` or the `double` keys**, never both. For example, Dataset PID has
  166,259 nodes with `long` and 61,498 with `double` coordinates. Read both as float.

### 3.3 Labels (counted over all files of each set)

| Node label | Dataset PID | OPEN100 | Synthetic |
|---|---|---|---|
| connector | 115,077 | 2,408 | 9,844 |
| crossing | 51,182 | 734 | 17,366 |
| valve | 28,262 | 257 | 630 |
| general | 17,600 | 234 | 3,806 |
| instrumentation | 11,979 | 350 | — |
| arrow | 1,657 | 451 | 59 |
| tank | — | 35 | 686 |
| pump | — | 16 | 421 |
| inlet/outlet | — | 96 | — |
| background | 2,000 | 48 | — |

| Edge label | Dataset PID | OPEN100 | Synthetic |
|---|---|---|---|
| solid | 242,117 | 4,567 | 28,399 |
| non-solid | 10,409 | — | 4,866 |

Nodes per drawing (min / mean / max): Dataset PID 301 / 456 / 729, OPEN100 181 / 386 / 675,
Synthetic 87 / 131 / 180. Edges: 337 / 505 / 793, 179 / 381 / 664, 87 / 133 / 184.

Compared with the paper's Table I (7 symbol classes: general, pump/compressor, arrow,
tank/vessel, instrumentation, inlet/outlet, valve):
- The files use the short names **`pump`** and **`tank`**.
- They have three extra labels that are not symbols:
  - `connector`: an 8 × 8 px box where a line meets a symbol;
  - `crossing`: an 8 × 8 px box where two lines cross;
  - `background`.
- **No set has all 7 classes.** Dataset PID has no pump, tank or inlet/outlet. Synthetic has no
  instrumentation or inlet/outlet. Only OPEN100 has inlet/outlet.
- OPEN100 has only `solid` lines, as the paper says.

### 3.4 Box sizes (median width × height in px)

| Label | Dataset PID | OPEN100 | Synthetic |
|---|---|---|---|
| valve | 66 × 65 | **20 × 22** | 45 × 45 |
| general | 57 × 60 | 14 × 12 | 136 × 136 |
| instrumentation | 116 × 116 | 43 × 42 | — |
| pump | — | 68 × 57 | 100 × 99 |
| tank | — | 187 × 177 (max width 750) | 161 × 166 |
| arrow | 54 × 53 | 12 × 12 | 48 × 90 |
| inlet/outlet | — | 200 × 44 | — |

Symbols in the real drawings are **much smaller** (a valve is about 20 px) than in the synthetic
ones, so a model trained on synthetic data meets a different scale on real data.

### 3.5 `background` boxes and the only invalid boxes
- `background` boxes are large strips along the drawing's edges. In Dataset PID `0.graphml` one
  is (0, 0)–(400, 4562), a left strip, and another is (0, 0)–(7168, 300), a top strip. In OPEN100
  `0.graphml` one is (2225.62, 3.28)–(2604, 1744), a right strip. **(inference)** They mark areas
  outside the diagram, such as the frame and title block, so they are not symbols.
- **Box check** (inside the image, `xmin ≤ xmax`, `ymin ≤ ymax`) over all 265,198 boxes: every
  symbol, connector and crossing box is valid. The only failures (501) are `background` boxes:
  - **Dataset PID: 500 files, 1 each.** The bottom strip is stored upside down, e.g.
    `ymin=4562, ymax=4312` (by 250 px).
  - **OPEN100 `11.graphml`: 1.** A top strip has `xmax=2792` on a 2786 px wide image (6 px out).
  - A loader should drop or fix `background` boxes, not trust them.

## 4. Dataset-P&ID `.npy` files

Opened with `numpy.load(f, allow_pickle=False)`. All 500 folders have the same 7 files.

### 4.1 Plain arrays (no pickle, loaded and checked)

| File | dtype | Shape | Content (drawing 0) |
|---|---|---|---|
| `<n>_KeyValue.npy` | `<U23` (text) | (k, 2) | Title-block fields: `['PROJECT/LOCATION/ASSIGN', 'IPY-65-37']`, `['ORGANIZATION', 'P-0']`, … (10 rows) |
| `<n>_Table.npy` | `<U19` (text) | (r, 6) | Revision table: header `ISSUE, DATE, MADE, CHECK'D, APPRV'D, DESCRIPTION`, then rows like `A, 15/07/22, X.DD, NIA, Z.JDM, ISSUE CONSTR. REV.1` |
| `<n>_lines2.npy` | `int64` | (m, 5) | `x1, y1, x2, y2, flag` with flag 0 or 1. Drawing 0: 68 rows, x 327–6843, y 196–4366 |

The text is made up, as it is a synthetic dataset (e.g. dates like `19Mar09`).

**(inference)** `lines2` holds the drawing's frame and table lines, not the pipes. Its first rows
are short vertical lines at x ≈ 6666–6738, y 4240–4336 (the table area). The nearest of its
points to any PID2Graph line point in drawing 0 is 250 px away (§6).

### 4.2 Pickled arrays: **not loaded**
Four files are NumPy **object arrays**. They can only be loaded with pickle, and
`allow_pickle=False` refuses them in all 2,000 files:

| File | Shape (drawing 0) | Row structure, read from the pickle listing |
|---|---|---|
| `<n>_symbols.npy` | (90, 3) | `id, [x1, y1, x2, y2], class`, e.g. `'symbol_1', [1669, 767, 1702, 829], '21'` |
| `<n>_words.npy` | (237, 4) | `id, [x1, y1, x2, y2], text, flag`, e.g. `'word_1', [1181, 2640, 1254, 2613], 'SDL', 0` |
| `<n>_lines.npy` | (186, 4) | `id, [x1, y1, x2, y2], line number, style`, e.g. `'line_1', [1783, 2793, 2068, 2793], '5"-EK-2648', 'solid'` |
| `<n>_linker.npy` | (90, 2) | `symbol id, [word ids, line id]`, e.g. `'symbol_11', ['word_1,word_2', 'line_75']` |

How this was read without running the pickle: the NumPy header (shape, dtype) was read with
`numpy.lib.format`, then the pickle bytes were listed with `pickletools.genops`. That lists the
instructions and does not run them. Two limits:
- Pickle stores a repeated value only once and refers back to it, so some values don't appear
  in the listing (e.g. the class of `symbol_2`). The full values need a real load.
- In `words`, `y1 > y2` in the example (2640 > 2613). The box corner order is not verified.

Safety check over all 2,000 pickled files: the only functions a load would import are
`numpy.core.multiarray._reconstruct`, `numpy.ndarray` and `numpy.dtype` (2,000 each). These are
the standard way NumPy saves object arrays. There is no `os`, `subprocess`, `eval` or other
import. The values are only lists, integers and strings. **Loading them is still the owner's
decision** (spec Requirement 7).

The class codes (`'21'`, `'2'`, …) are numbers. The paper (Fig. 3) shows 32 symbol types, but the
mapping from code to symbol name is **not in the files** we have.

## 5. Dataset-P&ID images and masks

| Folder | Files | Format | Sizes |
|---|---|---|---|
| `image_2/image_2/<n>.jpg` | 500 | JPEG, 3 colour components | 7168 × 4561 (300), 7168 × 4562 (200) |
| `mask/mask/<n>_mask.png` | 500 | PNG, 8-bit greyscale (colour type 0) | same as its own JPEG, checked pair by pair (0 mismatches) |

What the masks mark has not been checked yet. That needs looking at the pixels (Pillow/OpenCV,
still 🔜 Stage 6).

## 6. Open finding: is drawing N the same drawing in both datasets?

PID2Graph's `Dataset PID` folder is a converted copy of Dataset-P&ID. We have **not** been able
to confirm that number N means the same drawing in both:
- **Image size:** 310 of 500 pairs have the same size and 190 differ by 1 px in height. Both
  copies have the same mix (300 × 4561 and 200 × 4562), so the files are not simply numbered the
  same way. Alphabetical order (0, 1, 10, 100, …) does not fit either: 276/500 match, or 284 the
  other way round.
- **Coordinates, drawing 0:** the first original symbol is at (1669, 767)–(1702, 829). The first
  PID2Graph valves are at (2435, 932)–(2539, 1009) and (2720, 938)–(2807, 1007).
- The coordinate test with `lines2` proved nothing, because `lines2` seems to hold frame lines
  (§4.1). A real test needs `symbols`/`lines`, which need pickle.

**Consequence:** until this is checked, **never combine** PID2Graph boxes with original images
(or the reverse) by number. Use each dataset with its own images. This is the risk the owner's
decision (download the original images too) was meant to avoid.

## 7. For later steps
- **Phase 7 conversion:** map key IDs per file; read `long` and `double` coordinates; skip
  `background`; treat `connector`/`crossing` as graph points, not symbols.
- **Class sets differ between sets** (§3.3). The 7-class mapping of the original 32 codes is
  PID2Graph's choice, and the code-to-name list for the 32 codes is still missing.
- **Scale gap:** real symbols are about 20 px, synthetic ones 45–136 px (§3.4).
- **Evaluation:** only 12 real drawings (spec Open question 3 note).
