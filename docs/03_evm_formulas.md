# Earned Value Management (EVM): Formulas and Worked Examples

EVM is the core of **Module D (project controls)**. Every number in this file was checked with
Python in the project container (see section 9).

---

## 1. The idea in one picture

EVM compares **three numbers**, all expressed in money (or hours):

| Symbol | Name | Question |
|---|---|---|
| **PV** | Planned Value | How much work *should* be done by now? (from the baseline schedule) |
| **EV** | Earned Value | How much work *is actually* done, valued at its budget? |
| **AC** | Actual Cost | How much have we *actually spent* on the work done? |

Plus the total budget: **BAC** (Budget at Completion).

```
Money
 ▲                                  ╭──── PV (plan)
 │                              ╭───╯
 │                          ╭───╯     ● AC (spent: 460k)
 │                      ╭───╯  ● PV (500k)
 │                  ╭───╯      ● EV (earned: 380k)
 │             ╭────╯
 │       ╭─────╯
 └──────────────────────┬──────────────► Time
                    today (month 5)
EV < PV → behind schedule      EV < AC → over budget
```

**Why not just compare spent vs. planned?** Spending less than planned could mean you're
efficient *or* that you're behind. EV separates the two effects.

---

## 2. All formulas

### 2.1 Variances (in money)

| Metric | Formula | Good | Bad |
|---|---|---|---|
| **CV**: Cost Variance | EV − AC | > 0 under budget | < 0 over budget |
| **SV**: Schedule Variance | EV − PV | > 0 ahead | < 0 behind |

### 2.2 Performance indices (ratios)

| Metric | Formula | Meaning |
|---|---|---|
| **CPI**: Cost Performance Index | EV / AC | Value of work done per $1 spent. < 1 means over budget |
| **SPI**: Schedule Performance Index | EV / PV | Rate of progress vs. plan. < 1 means behind schedule |

### 2.3 Forecasts

| Metric | Formula | When to use |
|---|---|---|
| **EAC** (CPI method) | BAC / CPI | Current cost efficiency continues (the most common) |
| **EAC** (atypical) | AC + (BAC − EV) | The overrun was a one-time event; the rest goes to plan |
| **EAC** (CPI × SPI) | AC + (BAC − EV) / (CPI × SPI) | Both cost and schedule problems affect the remaining work (pessimistic) |
| **ETC**: Estimate to Complete | EAC − AC | Money still needed |
| **VAC**: Variance at Completion | BAC − EAC | Final overrun (negative) or underrun |
| **TCPI** (to meet BAC) | (BAC − EV) / (BAC − AC) | Efficiency needed on the remaining work to finish on budget |
| **TCPI** (to meet EAC) | (BAC − EV) / (EAC − AC) | Efficiency needed to finish at the EAC |

**TCPI rule of thumb:** if TCPI is much higher than the current CPI (for example by more than
about 0.1), finishing on the original budget is unrealistic.

---

## 3. Worked example

**Project:** a small pump station. BAC = **1,000,000**. Planned duration (PD) = **10 months**.

**Baseline plan (cumulative PV), an S-curve:**

| Month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| PV (k) | 50 | 120 | 220 | 350 | 500 | 650 | 780 | 880 | 950 | 1,000 |

**Status at the end of month 5 (AT = actual time = 5):**
- PV = 500,000 (from the plan)
- EV = 380,000 (38% of the work is physically complete × BAC)
- AC = 460,000 (from accounting)

### Step-by-step

| Metric | Calculation | Result | Interpretation |
|---|---|---|---|
| CV | 380,000 − 460,000 | **−80,000** | Spent 80k more than the work is worth |
| SV | 380,000 − 500,000 | **−120,000** | 120k worth of work behind the plan |
| CPI | 380,000 / 460,000 | **0.826** | Getting about 83 cents of work per dollar |
| SPI | 380,000 / 500,000 | **0.760** | Working at 76% of the planned rate |
| EAC (CPI) | 1,000,000 / 0.826 | **1,210,526** | Expected final cost |
| EAC (atypical) | 460,000 + 620,000 | **1,080,000** | Optimistic case |
| EAC (CPI × SPI) | 460,000 + 620,000 / (0.826 × 0.76) | **1,447,535** | Pessimistic case |
| ETC | 1,210,526 − 460,000 | **750,526** | Still needed |
| VAC | 1,000,000 − 1,210,526 | **−210,526** | Forecast overrun of about 21% |
| TCPI (BAC) | 620,000 / 540,000 | **1.148** | Would need to be 15% *more* efficient than plan, vs. 0.826 now → unrealistic |
| TCPI (EAC) | 620,000 / 750,526 | **0.826** | Equals the CPI (by definition of the CPI method) |

**Conclusion for the monthly report:** the project is over budget and behind schedule. The
forecast final cost is about 1.21M (range 1.08M–1.45M depending on the assumption). Recovering
to the original budget would need a big efficiency jump, which is unlikely. The client should be
warned and recovery actions planned.

---

## 4. Earned Schedule (ES): a better schedule measure

### The problem with SPI

SPI uses money, not time. **At the end of every project EV = PV = BAC, so SPI = 1.0**, even if
the project finished late. Near the end, SPI stops being meaningful.

> Example: our project finishes in month 12 instead of 10. At the end, SPI = 1,000,000 /
> 1,000,000 = **1.0** (looks perfect!), but the time-based SPI(t) = 10 / 12 = **0.833**
> (correctly shows it was late).

### Earned Schedule formulas

**ES** = the time at which the *planned* value equals the *current* earned value.

```
ES = C + (EV − PV_C) / (PV_C+1 − PV_C)
     C = the last whole period where PV ≤ EV
```

| Metric | Formula |
|---|---|
| **SPI(t)** | ES / AT |
| **SV(t)** | ES − AT (in time units) |
| **IEAC(t)**: forecast duration | PD / SPI(t) |

### Worked example (same project, month 5, EV = 380k)

1. Find C: PV at month 4 = 350k ≤ 380k < PV at month 5 = 500k, so **C = 4**.
2. ES = 4 + (380 − 350) / (500 − 350) = 4 + 30/150 = **4.2 months**
   → "the work done so far was planned to be finished at month 4.2".
3. SPI(t) = 4.2 / 5 = **0.84**
4. SV(t) = 4.2 − 5 = **−0.8 months** behind
5. IEAC(t) = 10 / 0.84 = **11.9 months** forecast duration (about 2 months late)

Note: SPI = 0.76 but SPI(t) = 0.84. They differ because the S-curve isn't linear. SPI(t) is in
time units and stays valid until the end of the project.

**Reference:** Lipke (2003), *Schedule is Different*; Vanhoucke's research at Ghent University
(the authors of our Module D dataset) compared these forecasting methods on real projects.

---

## 5. How EV is measured: progress and rules of credit

EV = % complete × budget. But how do you know the % complete? There are several methods:

| Method | How | Use for |
|---|---|---|
| **0/100** | 0% until finished, then 100% | Very short tasks |
| **50/50** | 50% at start, 50% at finish | Short tasks (1–2 periods) |
| **Weighted milestones (rules of credit)** | Fixed % per step | Engineering documents, procurement, equipment installation |
| **Units completed** | Installed quantity / total quantity | Concrete m³, pipe metres, cable metres |
| **Level of effort** | EV = PV (always "on schedule") | Management and support activities |

### Example: engineering drawings with rules of credit

Rules of credit (typical): Started 10% · IFR 40% · IFA 60% · IFC 90% · As-built 100%.

40 drawings, each budgeted at 100 hours (total 4,000 hours):

| Status | Count | Credit | Earned hours |
|---|---|---|---|
| IFC | 10 | 90% | 900 |
| IFA | 15 | 60% | 900 |
| IFR | 10 | 40% | 400 |
| Started | 5 | 10% | 50 |
| **Total** | **40** | | **2,250 (56.25% complete)** |

EV = 2,250 hours. If the plan said 2,600 hours by now, SPI = 2,250 / 2,600 = 0.87.

> **AI link:** document status (IFR/IFA/IFC) can come straight from the document register, so
> engineering progress can be calculated automatically (Module B + Module D).

### Procurement rules of credit (typical example)

MR issued 10% → PO placed 30% → vendor drawings approved 50% → FAT passed 80% → delivered to
site 100%.

---

## 6. Reading the indices together

| CPI | SPI | Situation | Typical action |
|---|---|---|---|
| > 1 | > 1 | Under budget, ahead | Check the baseline isn't too easy; keep going |
| > 1 | < 1 | Under budget, behind | Maybe under-resourced; add resources (you have budget room) |
| < 1 | > 1 | Over budget, ahead | Maybe over-resourced or paying overtime; slow the spend |
| < 1 | < 1 | Over budget, behind | **Critical:** recovery plan, warn management and client |

**Early stability:** research on EVM has found that the cumulative CPI tends to stabilize fairly
early in many projects. That makes early CPI-based forecasts useful, and it's one of the ideas
Module D tests on real data.

---

## 7. Common mistakes

| Mistake | Why it's wrong |
|---|---|
| Using the AC/PV ratio as "progress" | Spending isn't progress |
| Measuring EV by hours spent | That makes EV = AC, so CPI is always 1 |
| Trusting SPI near the end | It always goes to 1. Use SPI(t) |
| One EAC number only | Show a range (optimistic / CPI / CPI × SPI) |
| Not re-baselining after approved changes | The comparison becomes meaningless |
| Mixing commitments with actual cost | AC must be the cost of the work *performed* |

---

## 8. How Module D uses this

1. **Load** each real project's baseline and tracking periods (Ghent database).
2. **Compute** PV, EV, AC → CV, SV, CPI, SPI, ES, SPI(t), EAC (3 methods), VAC, TCPI per period.
3. **Forecast** the final cost and duration with ML, and compare it with the formulas above.
4. **Flag** risks (CPI < 0.9, SPI(t) < 0.9, TCPI − CPI > 0.1, three periods of decline).
5. **Report:** Python computes every number, then the LLM writes the narrative (it never does
   the math).

---

## 9. Python check (the code used to verify this file)

```python
BAC, PD, AT = 1_000_000, 10, 5
pv = [50, 120, 220, 350, 500, 650, 780, 880, 950, 1000]
pv = [x * 1000 for x in pv]
PV, EV, AC = pv[AT - 1], 380_000, 460_000

CPI, SPI = EV / AC, EV / PV                 # 0.8261, 0.7600
EAC = BAC / CPI                             # 1,210,526
EAC_pess = AC + (BAC - EV) / (CPI * SPI)    # 1,447,535
TCPI = (BAC - EV) / (BAC - AC)              # 1.1481

P = [0] + pv                                # cumulative PV with month 0
C = max(i for i in range(PD + 1) if P[i] <= EV)            # 4
ES = C + (EV - P[C]) / (P[C + 1] - P[C])                   # 4.2
SPI_t = ES / AT                                            # 0.84
IEAC_t = PD / SPI_t                                        # 11.90 months
```

This becomes `src/project_controls/evm.py` in Stage 5, with unit tests using these exact numbers.

---

## 10. Exercises

**Project X:** BAC = 2,000,000. At this status date: PV = 800,000, EV = 700,000, AC = 900,000.
Calculate CV, SV, CPI, SPI, EAC (CPI method), VAC and TCPI (BAC), then interpret them.

<details><summary>Answers</summary>

| Metric | Answer |
|---|---|
| CV | 700,000 − 900,000 = **−200,000** |
| SV | 700,000 − 800,000 = **−100,000** |
| CPI | 700,000 / 900,000 = **0.778** |
| SPI | 700,000 / 800,000 = **0.875** |
| EAC | 2,000,000 / 0.778 = **2,571,429** |
| VAC | 2,000,000 − 2,571,429 = **−571,429** (about 29% overrun) |
| TCPI | 1,300,000 / 1,100,000 = **1.182** |

Interpretation: over budget and behind schedule. Finishing on budget would need 18% better
efficiency than planned, against 22% *worse* so far, so it's unrealistic. Re-forecast and plan
recovery.
</details>

**Exercise 2:** a plan has cumulative PV of 100, 300, 600, 800, 1,000 over 5 months.
At month 4, EV = 450. Calculate ES and SPI(t).

<details><summary>Answers</summary>

C = 2 (PV month 2 = 300 ≤ 450 < PV month 3 = 600).
ES = 2 + (450 − 300) / (600 − 300) = 2 + 0.5 = **2.5 months**.
SPI(t) = 2.5 / 4 = **0.625** → the project is badly behind (1.5 months late after 4 months).
</details>
