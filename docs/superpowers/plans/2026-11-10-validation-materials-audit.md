# Validation and Material Prediction Evidence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` in the current session. Subagents are prohibited by the owner. Steps use checkbox (`- [x]`) tracking.

**Goal:** Audit two experimental-validation/material-prediction documents, separating formula inconsistencies, doping/sample mismatches, higher-order hydride evidence, and non-reproducible scoring from actual first-principles or experimental verification.

**Architecture:** A Python builder verifies four frozen assets, recomputes the printed formula through the existing spot-check function, and emits one `review.json`. The same object drives a claimed-versus-recomputed figure and `REVIEW.md`; docx-js uses the object and PNG to create the native Word report. Independent tests verify sources, numerical values, negative boundaries, and document structure.

**Tech Stack:** Python 3 standard library, unittest, Matplotlib, primary publisher/PMC/arXiv sources, vendored docx-js, native OMML, `kimi-word` OOXML validation and doc-k final-view rendering.

## Global Constraints

- Work only in `research/paper-direction-audit-2026-11-10/validation-materials/` and the specification/plan; keep both source documents and the spot-check script read-only.
- Use the four SHA-256 values in the specification; abort on drift. `research_program_count=1` with four method families.
- H3S computed `161.081843791778823 K`, H-S-Cl computed `237.894818964651591 K`; these are formula spot checks, not replacement predictions.
- Preserve Grockowiak's real 556 K report only as an irreversible higher-order/substituted-hydride claim with explicit experimental caveats, not binary LaH₁₀ routine validation.
- Preserve LaNiO₂ only in the correctly doped La1−xCaxNiO2 context `0.15 < x < 0.3`; undoped films are insulating.
- No global fit, new first-principles result, prediction replacement, experimental certification, or full-document/full-repository audit claim.
- Do not call unverified content fraudulent. Run doc-k once on the final artifact; no retry on exit 4/5/6 and no LibreOffice.

---

### Task 1: Missing-review RED

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/validation-materials/test_validation_materials_audit.py`
- Create: `research/paper-direction-audit-2026-11-10/validation-materials/run.log`

**Interfaces:** future `review.json`, `REVIEW.md`, `REVIEW.docx`; `run_all_tests() -> int`.

- [x] **Step 1: Write contracts before evidence exists**

Create tests for:

```python
def test_numeric_spotcheck(self):
    rows = self.data["evidence"]["formula_spotcheck"]
    self.assertAlmostEqual(rows["h3s"]["computed_tc_k"], 161.081843791778823)
    self.assertAlmostEqual(rows["h3s"]["claimed_tc_k"], 203.0)
    self.assertAlmostEqual(rows["h_s_cl"]["computed_tc_k"], 237.894818964651591)
    self.assertAlmostEqual(rows["h_s_cl"]["claimed_tc_k"], 320.0)
    self.assertFalse(rows["h_s_cl"]["is_first_principles_result"])

def test_lanio2_doping_scope(self):
    row = self.data["evidence"]["lanio2"]
    self.assertEqual(row["superconducting_dome"], [0.15, 0.3])
    self.assertTrue(row["undoped_insulating"])
    self.assertFalse(row["undoped_tc_20_40_verified"])

def test_grockowiak_role(self):
    row = self.data["evidence"]["grockowiak"]
    self.assertEqual(row["initial_tc_k"], 294)
    self.assertEqual(row["maximum_onset_tc_k"], 556)
    self.assertTrue(row["irreversible_higher_order"])
    self.assertFalse(row["meissner_completed"])
    self.assertFalse(row["binary_lah10_routine_validation"])
```

Add checks for all four hashes, Cl values 161/136 K and pressure 200 GPa, no scoring rubric, four direction IDs, all six false boundaries, and Markdown/Word structure. Word must contain native `m:oMath`, TOC, at least four tables, PAGE, a media image, Chinese header, and source footnotes for Frontiers, PMC, arXiv and `numeric_spotcheck.py`.

- [x] **Step 2: Run intentional RED**

Run `python research/paper-direction-audit-2026-11-10/validation-materials/test_validation_materials_audit.py -v`. Expected: exit 1 with `FileNotFoundError: review.json`. Save the full failure to `run.log`.

- [x] **Step 3: Commit specification and failing contract**

```bash
git add docs/superpowers/specs/2026-11-10-validation-materials-audit-design.md docs/superpowers/plans/2026-11-10-validation-materials-audit.md research/paper-direction-audit-2026-11-10/validation-materials/test_validation_materials_audit.py research/paper-direction-audit-2026-11-10/validation-materials/run.log
git commit -m "test: define validation and materials audit contracts"
```

---

### Task 2: Evidence object, figure, and source verification

**Files:**
- Create: `build_review.py`, `verify_primary_sources.py`
- Generate: `review.json`, `formula-spotcheck.svg`, `formula-spotcheck.png`, `REVIEW.md`

**Interfaces:**
- `build_data() -> dict`: sole evidence object.
- `build_figure(data) -> None`: two claimed-versus-computed groups.
- `build_markdown(data) -> str`: same evidence, no second fact database.
- `verify_primary_sources.run_all_tests() -> int`: independent checks.

- [x] **Step 1: Verify frozen assets and recompute formula**

Resolve both documents and `numeric_spotcheck.py`, verify hashes, and import `simplified_tc` with `importlib.util.spec_from_file_location`. Call it with `(1200, 2.0, 0.13)` and `(1500, 2.5, 0.12)`. Store exact outputs and claimed 203/320. Do not edit the spot-check script.

- [x] **Step 2: Encode primary-source roles and boundaries**

Record La1−xCaxNiO2 dome `[0.15, 0.3]`, undoped insulating, and `undoped_tc_20_40_verified=False`. Record Grockowiak 294→556 K, irreversible higher-order, no Meissner and no reliable high-temperature H–T diagram; set `binary_lah10_routine_validation=False`. Record Cl 6.25%→161 K and 12.5%→136 K at 200 GPa, with lower stabilization pressure as a separate effect. Set scoring rubric absent and all six open boundaries false.

- [x] **Step 3: Generate figure and Markdown**

Plot two groups: H3S claimed 203 vs computed 161.081843791778823, H-S-Cl claimed 320 vs computed 237.894818964651591. Title the figure `文中值与文中公式复算值：不是材料预测`. Label all four values and show units K. Save deterministic SVG and 220-dpi PNG. Insert figure after the formula table and before interpretation; state the insertion order.

Include source hashes, four direction rows, numeric table, doping scope, Grockowiak caveats, Cl direction, scoring limits, and explicit `全库审计尚未完成`.

- [x] **Step 4: Independently verify sources**

In `verify_primary_sources.py`, read `sources/primary-source-excerpts.md` and assert the dome, undoped-insulating statement, Grockowiak initial/max/onset and missing Meissner, Cl values and pressure, and formula outputs. Run both scripts. Expected: source checks pass; the main contract may fail only because DOCX is absent. Append actual outputs and exit codes to `run.log`.

---

### Task 3: Native Word with figure and primary-source footnotes

**Files:**
- Create: `build_report.js`, `.gitignore`
- Generate: `REVIEW.docx`, `word-qa/report.json`

**Interfaces:** consumes only `review.json` and `formula-spotcheck.png`.

- [x] **Step 1: Implement the docx-js report**

Use explicit CJK font channels, A4 margins, visible cached TOC plus real TOC field, Chinese header, PAGE-only footer, stable DXA tables, native Math API, and `features.updateFields=true`. Include source/direction, formula, doping/Grockowiak, correction, and open-boundary tables. Insert PNG immediately after the formula table with natural aspect ratio and caption. Add native footnotes for Frontiers, PMC, arXiv and `numeric_spotcheck.py`.

Create the simplified temperature formula with `MathFraction`/`MathSubScript`. Do not render it as an image. `.gitignore` excludes `node_modules/`, `__pycache__/`, QA PNGs and temporary files.

- [x] **Step 2: Build and run contracts**

```bash
PATH="/c/Program Files/nodejs:$PATH" python "{kimi-word}/scripts/docx.py" check-docx /absolute/path/validation-materials
PATH="/c/Program Files/nodejs:$PATH" python "{kimi-word}/scripts/docx.py" build /absolute/path/validation-materials/build_report.js /absolute/path/validation-materials/REVIEW.docx
python research/paper-direction-audit-2026-11-10/validation-materials/test_validation_materials_audit.py -v
python research/paper-direction-audit-2026-11-10/validation-materials/verify_primary_sources.py -v
```

Expected: OOXML and all tests pass. Do not filter build output.

- [x] **Step 3: Render and inspect once**

Run `docx.py render` once. If successful, read contact sheet first, then every page and every content-loss/near-blank finding. Record observations and final DOCX SHA-256. On exit 4/5/6, record unavailable visual QA without retry.

---

### Task 4: Final regression and named-branch delivery

- [x] **Step 1: Fresh verification**

Run both test suites, JSON parsing for `review.json` and QA report, `docx.py validate`, and `git diff --check`. Require exit 0 for each and append commands/outputs to `run.log`.

- [x] **Step 2: Commit and push**

```bash
git add research/paper-direction-audit-2026-11-10/validation-materials docs/superpowers/plans/2026-11-10-validation-materials-audit.md
git commit -m "docs: audit validation and material prediction evidence"
git push -u origin audit/room-temp-validation-materials
git rev-parse HEAD
git ls-remote origin refs/heads/audit/room-temp-validation-materials
```

Require matching hashes and a clean worktree. Do not merge. Close only this two-document audit; leave the remaining room_temp_sc and repository audit open.

## Plan Self-Review

- All four required issue families have primary-source roles and independent tests.
- The numerical spot check is separated from first-principles computation and material prediction.
- 556 K is preserved without deletion or binary-LaH₁₀ escalation; doped and undoped LaNiO₂ are distinguished.
- Scoring is treated as non-reproducible governance labels, not scientific percentages.
- Markdown and Word share one JSON and figure; native equations, tables, footnotes and final-view QA are verified.
