# EPC Fundamentals

Study notes for Stage 1. They explain how EPC projects work and **where AI can help**.
Terms in **bold** are in the [glossary](02_glossary.md). Earned value math is in
[03_evm_formulas.md](03_evm_formulas.md).

> Note: practices differ between companies and countries. Values marked "typical" are common
> examples, not universal rules. Every company defines its own procedures.

---

## Contents

1. [What is EPC?](#1-what-is-epc)
2. [Project delivery models](#2-project-delivery-models)
3. [Contract types and risk](#3-contract-types-and-risk)
4. [Project lifecycle](#4-project-lifecycle)
5. [Engineering and its documents](#5-engineering-and-its-documents)
6. [Specifications (MasterFormat and UFGS)](#6-specifications-masterformat-and-ufgs)
7. [Procurement](#7-procurement)
8. [Construction, commissioning and handover](#8-construction-commissioning-and-handover)
9. [Document control](#9-document-control)
10. [Project controls](#10-project-controls)
11. [Risk management and why projects overrun](#11-risk-management-and-why-projects-overrun)
12. [The PMI paper: delivering to cost](#12-the-pmi-paper-delivering-to-cost)
13. [Where AI fits in EPC](#13-where-ai-fits-in-epc)
14. [Self-check questions](#14-self-check-questions)

---

## 1. What is EPC?

**EPC = Engineering, Procurement and Construction.** One company (the **EPC contractor**)
takes responsibility for:

| Letter | Phase | In simple words |
|---|---|---|
| **E** | Engineering | Design the facility: calculations, drawings, specifications |
| **P** | Procurement | Buy everything: equipment, materials, subcontracts |
| **C** | Construction | Build it, install it, test it, hand it over working |

**Typical EPC projects:** oil and gas plants, refineries, petrochemical plants, power plants
(gas, solar, wind), water and wastewater treatment plants, LNG terminals, pipelines, mining
facilities, large infrastructure.

**Main parties:**

| Party | Role |
|---|---|
| **Owner / Client / Employer** | Pays for the project and will operate the facility |
| **EPC contractor** | Designs, buys and builds; often a consortium of several companies |
| **PMC** (Project Management Consultant) | Represents the owner and supervises the contractor |
| **Licensor** | Owns a process technology (e.g. a refining process) and provides the basic design |
| **Vendors / suppliers** | Manufacture and deliver equipment and materials |
| **Subcontractors** | Do parts of the construction (civil, electrical, insulation…) |
| **Lenders / insurers** | Finance or insure the project; often want a fixed price and date |
| **Authorities** | Issue permits and approvals |

**Why owners like EPC:** a **single point of responsibility** (one contractor to hold
accountable) and, usually, a **fixed price and fixed completion date**. That makes the project
easier to finance.

---

## 2. Project delivery models

| Model | How it works | Who carries design risk | Notes |
|---|---|---|---|
| **DBB** (Design-Bid-Build) | The owner hires a designer; the finished design is tendered to builders | Owner | Traditional; slow (design must finish before construction) |
| **DB** (Design-Build) | One contractor designs and builds | Contractor | Common in buildings and infrastructure |
| **EPC / LSTK** (Lump-Sum Turnkey) | One contractor does E, P and C for a fixed price, then hands over a working plant ("turn the key") | Contractor | Most risk on the contractor; common in process and power plants |
| **EPCM** (EPC Management) | The contractor does engineering and *manages* procurement and construction on the owner's behalf; the owner signs the purchase orders and subcontracts | Mostly owner | Usually reimbursable; the contractor earns a fee |
| **Alliance / collaborative** | Owner and contractors share pain and gain | Shared | Used for very complex or uncertain projects |

**Key idea:** the more risk the contractor carries, the higher its price (it adds
**contingency**), and the more important **cost control** becomes for the contractor.

---

## 3. Contract types and risk

| Type | Payment | Contractor's risk | Typical use |
|---|---|---|---|
| **Lump sum (fixed price)** | One fixed price for the defined scope | **High.** Overruns reduce its profit | Well-defined scope |
| **Reimbursable (cost-plus)** | Actual costs plus a fee (fixed or %) | Low; the owner pays overruns | Early or uncertain scope |
| **Unit rate** | Price per unit (per m³ of concrete, per metre of pipe) × actual quantity | Medium; quantity risk on the owner | Construction work with uncertain quantities |
| **GMP** (Guaranteed Maximum Price) | Reimbursable up to a cap; savings may be shared | Medium–high | Buildings |
| **Convertible** | Starts reimbursable (during FEED), converts to lump sum once the scope is clear | Changes over time | Large process plants |

**Standard contract forms:** many international EPC contracts are based on **FIDIC** forms.
The **FIDIC Silver Book** is the form for EPC/Turnkey projects (most risk on the contractor),
and the **Yellow Book** is for plant and design-build. Other families include NEC (UK) and
AIA/ConsensusDocs (USA).

**Important contract terms:**
- **Scope of work:** exactly what is included. Anything outside it is a **change** (variation).
- **Liquidated damages (LDs):** money the contractor pays per day of delay or for performance
  shortfalls.
- **Performance guarantees:** the plant must reach its guaranteed capacity and efficiency.
- **Change order / variation:** a formal change to scope, price or time.
- **Warranty / defects liability period:** the contractor fixes defects after handover.

> **Why this matters for AI:** on a lump-sum project, every engineering hour wasted searching
> documents and every late warning about a cost overrun is lost profit for the contractor.

---

## 4. Project lifecycle

```
 Idea → Feasibility → Pre-FEED → FEED ──► EPC award ──► Detailed engineering
                                                         Procurement          (overlap!)
                                                         Construction
                                    ──► Pre-commissioning → Commissioning → Start-up
                                    ──► Performance test → Handover → Warranty → Close-out
```

| Phase | What happens | Main outputs |
|---|---|---|
| Feasibility / concept | Is the project worth doing? Options studied | Business case, rough estimate (Class 5) |
| Pre-FEED | Select the best option | Selected concept, Class 4 estimate |
| **FEED** (Front-End Engineering Design) | Basic engineering for the chosen option | PFDs, main P&IDs, equipment list, plot plan, specs, **Class 3 estimate**, EPC tender package |
| EPC tendering and award | Contractors bid; the owner selects one | EPC contract |
| **Detailed engineering** | Complete design for construction | IFC drawings, datasheets, specs, MTOs, 3D model |
| **Procurement** | Buy equipment and materials | POs, vendor documents, deliveries |
| **Construction** | Build and install | Installed plant, quality records |
| **Mechanical completion** | Plant is built per design | MC certificate, punch list |
| **Pre-commissioning / commissioning** | Test systems (flushing, loop checks, energizing), then run them with real fluids | Commissioning records |
| **Start-up and performance test** | Plant operates; guarantees are tested | Performance test report |
| **Handover** | The owner takes over | Handover certificate, as-built documents, O&M manuals |
| Close-out | Final accounts, claims, lessons learned | Final account, close-out report |

**Front-End Loading (FEL):** many owners use stage gates (FEL-1, FEL-2, FEL-3, roughly
feasibility → pre-FEED → FEED). The project only continues when a gate is approved.

**Key insight:** in EPC, engineering, procurement and construction **overlap** (fast-tracking).
Construction can start while engineering is still running. This saves time but creates
**interface risk**: a late engineering change can hit equipment already ordered or concrete
already poured.

---

## 5. Engineering and its documents

### 5.1 Engineering disciplines

| Discipline | Designs | Typical deliverables |
|---|---|---|
| **Process** | How the plant works chemically and physically | PFD, heat and material balance, process datasheets, P&IDs (with piping) |
| **Mechanical: static** | Vessels, tanks, heat exchangers | Mechanical datasheets, vessel drawings |
| **Mechanical: rotating** | Pumps, compressors, turbines | Datasheets, specifications |
| **Piping** | Pipes, routing, supports | Plot plan, piping GA, isometrics, line list, piping specs (classes) |
| **Civil / structural** | Foundations, steel structures, buildings, roads | Foundation drawings, steel drawings, calculations |
| **Electrical** | Power distribution, cables, lighting | Single-line diagram (SLD), cable schedule, load list |
| **Instrumentation and control (I&C)** | Instruments, control system, safety system | Instrument index, instrument datasheets, loop diagrams, cause and effect charts |
| **HVAC / architecture / HSE** | Buildings, ventilation, fire and safety | Layouts, fire and gas layouts, hazardous area classification |

### 5.2 Key documents and how they flow

```
Process design:   PFD → Heat & material balance → P&IDs
                                     │
                    ┌────────────────┼──────────────────┐
                    ▼                ▼                  ▼
            Equipment list      Line list         Instrument index
                    │                │                  │
              Datasheets      Piping GA/3D model   Instrument datasheets
                    │                │                  │
               Requisitions     Isometrics          Loop diagrams
               (procurement)   (construction)
```

| Document | What it shows |
|---|---|
| **PFD** (Process Flow Diagram) | Main process flows and equipment; no small details |
| **P&ID** (Piping & Instrumentation Diagram) | Every pipe, valve, instrument and control loop, with **tag numbers**. It is the "master" engineering document. |
| **Datasheet** | Technical requirements for one item (pump flow, pressure, materials…) |
| **Equipment list / line list / instrument index** | Tables of all equipment, pipes and instruments |
| **Plot plan / GA** (General Arrangement) | Where things are located |
| **Isometric** | One pipe line drawn in 3D-style view, used for fabrication and construction |
| **Specification** | Written technical requirements (materials, workmanship, testing) |
| **MTO** (Material Take-Off) | Quantities of material to buy, measured from drawings and models |
| **Calculation** | Engineering calculations (structural, hydraulic, cable sizing…) |

**Tag numbers:** every item has a unique tag, e.g. `P-101A` (pump 101 A), `V-201` (vessel),
`FIC-1001` (Flow Indicating Controller 1001), `PSV-305` (pressure safety valve). Instrument
tags follow the ISA-5.1 standard: the first letter is the measured variable (F = flow,
P = pressure, T = temperature, L = level) and the following letters are the functions
(I = indicate, C = control, T = transmit…).
→ **Module C** reads these tags from drawings.

### 5.3 Document status and revisions (typical)

| Status | Meaning |
|---|---|
| **IFR**: Issued for Review | First issue, sent to the client for comments |
| **IFA**: Issued for Approval | Comments incorporated; sent for formal approval |
| **AFD**: Approved for Design | Can be used by other disciplines |
| **IFC**: Issued for Construction | Final, can be built from |
| **As-built** | Updated to show what was actually built |

**Revisions:** often letters during review (A, B, C…), then numbers after approval (0, 1, 2…).

**Client review codes (typical):** Code 1 = approved; Code 2 = approved with comments;
Code 3 = rejected, revise and resubmit; Code 4 = for information only.

> **Why this matters for AI:** a large EPC project can produce tens of thousands of documents,
> each with revisions and comments. Classifying, searching and extracting from them is a big
> manual effort (→ Modules A and B).

---

## 6. Specifications (MasterFormat and UFGS)

A **specification** says *what quality* is required: materials, standards, workmanship,
testing, submittals. Drawings say *what and where*; specifications say *how good*.

### 6.1 MasterFormat

**MasterFormat** (by CSI and CSC, North America) organizes construction specifications into
numbered **divisions** and **sections**. A section number has the form `03 30 00`
(division 03, Concrete → 30 Cast-in-Place Concrete).

| Division | Title | Division | Title |
|---|---|---|---|
| 01 | General Requirements | 22 | Plumbing |
| 02 | Existing Conditions | 23 | HVAC |
| 03 | Concrete | 25 | Integrated Automation |
| 04 | Masonry | 26 | Electrical |
| 05 | Metals | 27 | Communications |
| 06 | Wood, Plastics, Composites | 28 | Electronic Safety and Security |
| 07 | Thermal and Moisture Protection | 31 | Earthwork |
| 08 | Openings | 32 | Exterior Improvements |
| 09 | Finishes | 33 | Utilities |
| 10 | Specialties | 34 | Transportation |
| 11 | Equipment | 35 | Waterway and Marine Construction |
| 12 | Furnishings | 40 | Process Interconnections |
| 13 | Special Construction | 41 | Material Processing and Handling Equipment |
| 14 | Conveying Equipment | 43 | Process Gas and Liquid Handling |
| 21 | Fire Suppression | 46 | Water and Wastewater Equipment |

→ **Module B** uses the division as the class label for document classification.

### 6.2 The three-part section format

Every section has the same structure:

| Part | Contains | Example articles |
|---|---|---|
| **PART 1 GENERAL** | Administrative requirements | References (standards), definitions, **submittals**, quality assurance, delivery/storage/handling |
| **PART 2 PRODUCTS** | Materials and equipment | Materials, mixes, components, fabrication, factory tests |
| **PART 3 EXECUTION** | How to install and check | Preparation, installation, field quality control, tests, protection |

Articles are numbered `1.1`, `1.2`, `2.3`, `3.9`, with sub-articles `3.9.1`.
→ **Module A** chunks the specs along exactly this structure.

### 6.3 UFGS (our real data)

**UFGS** (Unified Facilities Guide Specifications) are the U.S. Department of Defense's
construction specifications, published free on wbdg.org in MasterFormat structure.
They are real, detailed, cover all divisions, and are public domain, which makes them ideal for
this project.

UFGS classifies required submittals with **SD codes** (defined in section 01 33 00), for example:

| Code | Submittal type |
|---|---|
| SD-01 | Preconstruction submittals |
| SD-02 | Shop drawings |
| SD-03 | Product data |
| SD-04 | Samples |
| SD-05 | Design data |
| SD-06 | Test reports |
| SD-07 | Certificates |
| SD-08 | Manufacturer's instructions |
| SD-09 | Manufacturer's field reports |
| SD-10 | Operation and maintenance data |
| SD-11 | Closeout submittals |

→ **Module B** can extract the required submittals per section into a **submittal register**,
a real task that document controllers do by hand.

**Referenced standards** appear in PART 1 "References": ASTM (materials testing), ACI
(concrete), AISC (steel), ASME (pressure equipment and piping), API (oil and gas), IEEE / NFPA
(electrical and fire), ISO.

---

## 7. Procurement

Procurement often makes up a large share of EPC cost, especially in process plants where
equipment is expensive. Late equipment is one of the most common causes of delay.

### 7.1 The procurement cycle

```
Engineering                      Procurement                               Site
───────────                      ───────────                               ────
Datasheet + spec ──► MR ──► Bidders list ──► RFQ ──► Bids ──► TBE + CBE ──► Award (PO)
                                                                              │
     Vendor documents (VDR) ◄── review by engineering ◄──────────────────────┤
                                                                              ▼
                                  Expediting ──► Inspection / FAT ──► Shipping ──► Site receipt (MRR)
```

| Step | Meaning |
|---|---|
| **MR** (Material Requisition) | The engineering request to buy: technical requirements, quantity, documents required |
| **AVL / bidders list** | Approved vendors allowed to bid |
| **RFQ / ITB** | Request for Quotation / Invitation to Bid sent to vendors |
| **TBE** (Technical Bid Evaluation) | Engineers check each bid's compliance with the spec, often with a list of **deviations** and **clarifications** |
| **CBE** (Commercial Bid Evaluation) | Price, payment terms, delivery time, warranty |
| **Bid tabulation** | Side-by-side comparison of all bids |
| **PO** (Purchase Order) | The contract with the selected vendor |
| **VDR / VDRL** | Vendor Document Requirements List: drawings, calculations and manuals the vendor must submit for review |
| **Expediting** | Following up to keep the vendor on schedule |
| **Inspection / FAT** | Quality inspections at the factory; Factory Acceptance Test |
| **Logistics** | Shipping, customs, **Incoterms** (who pays and carries risk during transport, e.g. FOB, CIF, DAP, DDP) |
| **MRR / OS&D** | Material Receiving Report at site / Overage, Shortage and Damage report |

**Long-lead items:** equipment with long manufacturing times (large compressors, transformers,
turbines, heavy vessels). They are ordered first, sometimes even before the EPC award.

> **Why this matters for AI:** comparing a vendor bid against a 100-page specification (the TBE)
> is slow and error-prone. An LLM can pre-check compliance and list the deviations
> (→ Modules A and B, Stage 7).

---

## 8. Construction, commissioning and handover

### 8.1 Typical construction sequence

Mobilization → site preparation and earthworks → underground (piping, cables, grounding) →
foundations → structural steel → equipment setting → piping → electrical and instrumentation →
insulation and painting → **mechanical completion**.

### 8.2 Construction documents

| Document | Purpose |
|---|---|
| **Method statement** | How a task will be done safely and correctly |
| **ITP** (Inspection and Test Plan) | Which inspections happen and who witnesses them (hold/witness points) |
| **RFI** (Request for Information) | A question from site to engineering when something is unclear or conflicting |
| **NCR** (Non-Conformance Report) | Work or material that does not meet the specification |
| **Daily / weekly report** | Manpower, equipment, progress, weather, issues, safety |
| **Permit to work** | Authorization for hazardous work (hot work, confined space…) |
| **Punch list** | Remaining defects. **Punch A** = must be fixed before the next step; **Punch B** = can be fixed later |
| **As-built drawings** | Drawings updated to match what was actually built |

### 8.3 Completion and handover

| Step | Meaning |
|---|---|
| **Mechanical completion (MC)** | Built and installed according to the design, static tests done |
| **Pre-commissioning** | Checks without process fluids: flushing, cleaning, loop checks, motor rotation |
| **Commissioning** | Systems run with real utilities and fluids |
| **RFSU** (Ready for Start-Up) | Plant is ready to introduce feed |
| **Performance test** | Proves the guaranteed capacity and efficiency |
| **Handover / provisional acceptance** | The owner takes control; the warranty starts |

Commissioning is organized by **systems and subsystems**, not by area. Completion tracking
needs systems such as "completions management".

> **Why this matters for AI:** RFIs, NCRs and daily reports are unstructured text written in a
> hurry. Classifying them, linking them to spec clauses and spotting trends (e.g. repeated
> concrete NCRs) is ideal for NLP (→ Modules B and E, Stage 7).

---

## 9. Document control

**Document control** makes sure everyone uses the right revision of every document.

| Concept | Meaning |
|---|---|
| **Document numbering** | e.g. `PRJ-100-ME-DS-0012`: project, area/unit, discipline, document type, sequence |
| **MDR** (Master Document Register) | The list of every document the project will produce, with planned and actual dates |
| **Transmittal** | The cover record when documents are formally sent between parties |
| **Revision control** | Only the latest approved revision is used; old ones are marked superseded |
| **Comment sheet / CRS** | Comment Resolution Sheet: the reviewer's comments and the responses |
| **EDMS** | Electronic Document Management System (e.g. Aconex, SharePoint, Documentum, AVEVA) |

> **Why this matters for AI:** automatic classification (type, discipline, area), metadata
> extraction from title blocks, and checking a document against the MDR are direct uses of
> Module B.

---

## 10. Project controls

**Project controls** = planning, measuring and forecasting **cost and schedule**, so management
can act early.

### 10.1 Breakdown structures

| Structure | Breaks down |
|---|---|
| **WBS** (Work Breakdown Structure) | The scope into deliverables / work packages |
| **CBS** (Cost Breakdown Structure) | Costs into cost accounts (labour, materials, equipment…) |
| **OBS** (Organizational Breakdown Structure) | Who is responsible |
| **RAM** (Responsibility Assignment Matrix) | WBS × OBS: who owns which work |
| **Control account** | The point where scope, budget, schedule and responsibility meet, and where EVM is measured |

### 10.2 Planning and scheduling

- **CPM** (Critical Path Method): activities, durations and logic links (FS, SS, FF, SF).
- **Critical path:** the longest chain of dependent activities. Any delay on it delays the
  project.
- **Float (slack):** how much an activity can slip without delaying the project.
- **Baseline:** the approved plan, frozen for comparison.
- **Schedule levels:** Level 1 (milestones) to Level 4/5 (detailed work).
- **Tools:** Primavera P6 (the standard in EPC), MS Project.
- **S-curve:** cumulative planned vs. actual progress or cost over time.

### 10.3 Cost estimating and budgets

**AACE estimate classes (Recommended Practice 18R-97, typical accuracy ranges):**

| Class | Project definition | Typical use | Expected accuracy (low / high) |
|---|---|---|---|
| 5 | 0–2% | Concept screening | −20 to −50% / +30 to +100% |
| 4 | 1–15% | Feasibility | −15 to −30% / +20 to +50% |
| 3 | 10–40% | Budget authorization (end of FEED) | −10 to −20% / +10 to +30% |
| 2 | 30–75% | Control / bid | −5 to −15% / +5 to +20% |
| 1 | 65–100% | Check estimate / bid | −3 to −10% / +3 to +15% |

**Cost terms:** budget, **commitment** (money promised in POs and subcontracts), **actual
cost** (money spent), **forecast / EAC**, **contingency** (for known-unknowns inside the scope),
**management reserve** (for unknown-unknowns).

### 10.4 Progress measurement

Physical progress is measured with **rules of credit**, for example engineering drawings:
started 10% → IFR 40% → IFA 60% → IFC 90% → as-built 100% (typical; each company defines its
own). These steps are weighted by budgeted hours to give **earned value**.
→ Full details and examples in [03_evm_formulas.md](03_evm_formulas.md).

### 10.5 Earned Value Management (summary)

| Metric | Question it answers |
|---|---|
| CPI = EV / AC | How much work do we get per dollar spent? |
| SPI = EV / PV | How fast are we working compared with the plan? |
| EAC = BAC / CPI | What will the total cost be at the end? |

→ **Module D** computes these for 133 real projects and tries to predict overruns early.

### 10.6 Change management

Change flow: **trend** (early warning) → **change notice / request** → estimate the impact
(cost and time) → approval → **change order / variation** → update the baseline.
Unmanaged changes are one of the biggest causes of lump-sum losses.

### 10.7 Reporting

A **monthly progress report** typically contains: executive summary, HSE statistics, progress
(planned vs. actual by discipline), S-curves, cost status (budget, committed, actual, EAC),
EVM indices, critical path and key milestones, procurement status, risks and issues, changes,
and look-ahead.
→ **Module D** generates this automatically: Python computes the numbers, the LLM writes the
narrative.

---

## 11. Risk management and why projects overrun

### 11.1 Risk management process

Identify → analyze (probability × impact) → plan the response (avoid, transfer, mitigate,
accept) → monitor.

- **Risk register:** a table of risks with owner, probability, impact, response and status.
- **Quantitative risk analysis:** **Monte Carlo** simulation of cost and schedule gives a
  probability distribution. **P50** = 50% chance of finishing under that value;
  **P90** = 90% chance. Contingency is often set from the gap between P50/P90 and the base
  estimate.

### 11.2 Common causes of cost and schedule overruns

| Cause | Example |
|---|---|
| Incomplete scope / poor FEED | Design changes after equipment is ordered |
| Late engineering | Construction waits for IFC drawings |
| Procurement delays | A long-lead compressor arrives 4 months late |
| Interface problems | Vendor data arrives late, so piping and civil designs change |
| Changes not controlled | Extra work done without a change order |
| Low productivity | Weather, congestion, labour shortages, rework |
| Optimistic estimate | The tender price was too low to win the contract |
| Logistics and permits | Customs, heavy transport, authority approvals |

Large projects overrunning their budgets and schedules is a well-documented pattern in project
management research. **Early detection** is the key to reducing the damage.

---

## 12. The PMI paper: delivering to cost

**Paper:** *Delivering to Cost in an EPC World* (PMI library title: *Realizing Engineering,
Procurement and Construction Projects*). Carlson, Cori, Junghans and Bredehoeft, CH2M Hill,
PMI Global Congress 2007, North America.

> Note: the full text is behind PMI membership. This summary is based on the published abstract
> and the standard EPC practice it describes.

**Topics covered (from the abstract):**
1. The challenge and the key success factors of delivering EPC projects to cost
2. A definition of "delivering to cost"
3. The EPC project manager's key responsibilities
4. The critical elements of an EPC project plan

**Main lessons, linked to this project:**

| Lesson | Project module |
|---|---|
| Cost control must start in engineering and procurement, not only on site | A, B: faster, more accurate engineering and procurement document work |
| A realistic baseline and integrated cost/schedule control | D: EVM engine |
| Detect deviations early, while there is still time to act | D: early overrun forecasting and risk flags |
| Strict change control | B/E: classify and track changes and RFIs |
| Regular, honest reporting | D: automatic monthly report |

---

## 13. Where AI fits in EPC

| EPC pain point | Who suffers | AI solution | Module |
|---|---|---|---|
| Searching long specs and standards takes hours | Engineers, site QA/QC | RAG assistant with citations | **A** |
| Sorting and registering thousands of documents | Document controllers | Automatic classification and metadata extraction | **B** |
| Building submittal registers and TBE compliance checks by hand | Document control, procurement | LLM extraction into structured JSON | **B** |
| Legacy drawings exist only as scanned images | Engineering, operations | P&ID digitization: symbols, tags, connectivity | **C** |
| Monthly reports take days to prepare and are already late | Project controls | Automatic EVM and report generation | **D** |
| Overruns are discovered too late | Management | ML forecasting and early-warning flags | **D** |
| Answers need data from many systems | Everyone | An agent that combines specs, documents, drawings and project data | **E** |
| RFIs, NCRs and daily reports are unstructured | Site and engineering | Classification, linking to spec clauses, trend detection | **B, E** |

**Business value to mention in interviews:** hours saved per engineer per week, fewer errors
(missed submittals, wrong revisions), earlier warnings (weeks earlier than manual reporting),
and better decisions.

**Limits to mention honestly:** AI assists people, it doesn't replace engineering judgment.
Answers must be cited and checked. Safety-critical decisions stay with qualified engineers.
Data confidentiality matters (client data, export control).

---

## 14. Self-check questions

Answer out loud first, then open the answer.

<details><summary>1. What does EPC mean, and why do owners like it?</summary>
Engineering, Procurement and Construction by one contractor. Owners get a single point of
responsibility and usually a fixed price and date, which helps financing.
</details>

<details><summary>2. Difference between EPC (LSTK) and EPCM?</summary>
In LSTK the contractor carries the cost and schedule risk for a fixed price. In EPCM the
contractor manages procurement and construction on the owner's behalf (usually reimbursable),
so the owner carries most of the risk.
</details>

<details><summary>3. Why is cost control critical for a lump-sum contractor?</summary>
The price is fixed, so every overrun comes directly out of the contractor's profit.
</details>

<details><summary>4. What is FEED and what does it produce?</summary>
Front-End Engineering Design: basic engineering for the chosen concept. It produces PFDs, main
P&IDs, the equipment list, specs, a Class 3 estimate and the EPC tender package.
</details>

<details><summary>5. What is a P&ID, and what does tag FIC-1001 mean?</summary>
Piping & Instrumentation Diagram: all pipes, valves, instruments and control loops. FIC = Flow
Indicating Controller, loop number 1001.
</details>

<details><summary>6. What are PART 1, 2 and 3 in a specification section?</summary>
PART 1 General (references, submittals, QA), PART 2 Products (materials and equipment),
PART 3 Execution (installation, field quality control, testing).
</details>

<details><summary>7. Describe the procurement cycle.</summary>
MR → bidders list → RFQ → bids → TBE + CBE → PO → vendor documents (VDR) → expediting →
inspection/FAT → shipping → site receipt.
</details>

<details><summary>8. What is the difference between an RFI and an NCR?</summary>
An RFI is a question to engineering about unclear or conflicting information. An NCR records
work or material that doesn't meet the specification.
</details>

<details><summary>9. CPI = 0.85 and SPI = 1.05. What does that mean?</summary>
Over budget (85 cents of work per dollar spent) but slightly ahead of schedule.
</details>

<details><summary>10. Name 5 causes of EPC overruns.</summary>
Poor FEED / scope changes, late engineering, procurement delays, uncontrolled changes, low
productivity / rework (also: optimistic estimates, interfaces, logistics).
</details>

<details><summary>11. Give one AI use case for each of E, P and C.</summary>
E: RAG over specs, or P&ID digitization. P: automatic TBE compliance check of vendor bids.
C: classifying NCRs and RFIs and linking them to spec clauses. Controls: automatic EVM report
and overrun forecast.
</details>
