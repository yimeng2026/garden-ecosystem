# Physical Intuition Direction Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` in the current session. Subagents are prohibited by the owner. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Produce an evidence-gated audit of the two physical-intuition documents, distinguishing one research lineage and four candidate direction families from completed, unconverged, and unstarted work.

**Architecture:** A Python builder reads the current source documents and frozen numerical summaries, computes source hashes and evidence records, and emits one `review.json`. The same object drives an H0 figure and Markdown report. A docx-js renderer consumes that object and figure to create a native Word report, followed by independent content, OOXML, and final-view checks.

**Tech Stack:** Python 3.12 standard library, unittest, Matplotlib, vendored docx-js 9.7.1 with native Math API, OOXML, `kimi-word` validation and doc-k final-view rendering.

## Global Constraints

- Work only in `research/paper-direction-audit-2026-11-10/physical-intuition/` and this plan in the isolated garden worktree.
- Do not modify or restore the provider worktree, especially its uncommitted `MATH_PHYSICS_WORLDVIEW_2026.md` and unrelated scripts.
- Preserve both source hashes exactly: `89fc5499acd3f5afd05ffd0b4eacae3f40d33822802679a3c105d34acc0f9eb4` and `91f6653c273c3783e9fc71ef8b9b64463a038fecd5763633038e601d93ae862d`.
- Treat the two documents as one research lineage. Use four candidate direction families, not 36 independent directions.
- Fixed zero-model results are not a full-parameter posterior, global optimum, or no-CDM-family exclusion. The physical-intuition engine remains unvalidated.
- Do not install dependencies or rerun the full CLASS/CAMB/CosmoMC pipeline. Use the frozen summaries and the actual 41-test suite.

---

### Task 1: Baseline and Missing-Data RED

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/physical-intuition/test_physical_intuition_audit.py`
- Create: `research/paper-direction-audit-2026-11-10/physical-intuition/run.log`

**Interfaces:**
- Consumes: future `review.json`, `REVIEW.md`, and `REVIEW.docx`.
- Produces: five independent contract tests and `run_all_tests()`.

- [ ] **Step 1: Run the actual 41-test baseline**

Run from the provider worktree:

```bash
python -m unittest discover -s research/physical-intuition/zero-cdm/tests -p "test*.py" -v
```

Expected: exit 0, with `Ran 41 tests` and `OK` in the output. Save the command and key output to `run.log`. Do not modify provider files.

- [ ] **Step 2: Write the contract test before the report exists**

```python
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PhysicalIntuitionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_direction_count(self):
        self.assertEqual(len(self.data["sources"]), 2)
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(len({row["id"] for row in self.data["directions"]}), 4)

    def test_frozen_source_hashes(self):
        expected = {
            "physical-intuition:research/physical-intuition/MATH_PHYSICS_WORLDVIEW_2026.md": "89fc5499acd3f5afd05ffd0b4eacae3f40d33822802679a3c105d34acc0f9eb4",
            "physical-intuition:research/physical-intuition/TOTAL_PROJECT_2026-11-08/TOTAL_REPORT.md": "91f6653c273c3783e9fc71ef8b9b64463a038fecd5763633038e601d93ae862d",
        }
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, expected)

    def test_h0_slice_is_not_global_fit_and_does_not_trigger_expansion(self):
        h0 = self.data["evidence"]["h0_scan"]
        self.assertEqual(h0["case_count"], 10)
        self.assertEqual(h0["minimum_h0"], 85.0)
        self.assertAlmostEqual(h0["minimum_delta_chi_squared"], 141291.74549083476, delta=1e-8)
        self.assertFalse(h0["expanded_scan_triggered"])
        self.assertFalse(h0["posterior_sampling_performed"])

    def test_open_boundaries_are_explicit(self):
        boundaries = self.data["open_boundaries"]
        self.assertFalse(boundaries["global_cosmological_fit_completed"])
        self.assertFalse(boundaries["nonlinear_matter_spectrum_completed"])
        self.assertFalse(boundaries["extreme_phase_sequence_converged"])
        self.assertFalse(boundaries["accuracy_boost_8_completed"])
        self.assertFalse(boundaries["physical_intuition_engine_validated"])

    def test_actual_test_count_and_other_observations(self):
        verification = self.data["evidence"]
        self.assertEqual(verification["unit_tests"], {"passed": 41, "total": 41})
        self.assertGreater(verification["planck_lensing"]["maximum_delta_chi_squared"], 1238.0)
        self.assertGreater(verification["full_cmb_hyrec"]["delta_chi_squared_total"], 179000.0)
        self.assertLess(verification["bbn"]["maximum_absolute_delta_chi_squared"], 0.005)

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        self.assertIn("不是整个无 CDM 模型族的排除", markdown)
        self.assertIn("物理直觉引擎尚未验证有效", markdown)
        self.assertIn("图 1", markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            document = package.read("word/document.xml")
            names = package.namelist()
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 2)
        self.assertIn(b"PAGE", footer)
        self.assertIn("物理直觉", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
```

- [ ] **Step 3: Run the missing-data RED**

Run: `python test_physical_intuition_audit.py -v`

Expected: exit 1 with `FileNotFoundError: review.json`. This is the intentional RED for missing deliverables. Save the complete output to `run.log`.

- [ ] **Step 4: Commit the baseline and failing contract**

```bash
git add research/paper-direction-audit-2026-11-10/physical-intuition/test_physical_intuition_audit.py research/paper-direction-audit-2026-11-10/physical-intuition/run.log docs/superpowers/plans/2026-11-10-physical-intuition-direction-audit.md
git commit -m "test: define physical intuition audit contracts"
```

---

### Task 2: Data-Driven Review, H0 Figure, and Markdown

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/physical-intuition/build_review.py`
- Generate: `review.json`, `h0-scan-comparison.svg`, `h0-scan-comparison.png`, `REVIEW.md`

**Interfaces:**
- Consumes: current source files and frozen summaries in the provider worktree.
- Produces: one evidence object shared by all report formats.

- [ ] **Step 1: Implement source resolution and evidence extraction**

Locate the provider directory by searching parents for `.worktrees/provider-main-integration/research/physical-intuition` and read it without modification. Compute both source hashes at build time. Read:

- `zero-cdm/planck-h0-scan-summary.json` for all ten cases, minimum H0/delta, expansion decision, and no-posterior flag;
- `zero-cdm/planck-lensing-cmbmarged-summary.json` for the three lensing deltas and extrema;
- `zero-cdm/planck-cmb-unbounded-hyrec-summary.json` for full-CMB delta and no-fit boundary;
- `zero-cdm/bbn-summary.json` for the maximum absolute observational delta;
- current Markdown only for role/lineage review, not for overwriting the provider file.

Store `source_lineage.research_program_count=1`, both sources, and these four direction IDs: `math_physics_methodology`, `zero_cdm_observation`, `crosscode_systematics`, `physical_intuition_engine`. Direction records contain `role`, `closed`, `unfinished`, `next`, and `status`, exactly matching the specification.

- [ ] **Step 2: Build the H0 figure from the same summary**

Use two panels: total χ² for zero/baseline on a log scale and paired zero-minus-baseline Δχ² on a log scale. Include the computational threshold 10 without calling it sigma. Mark the H0=85 minimum and title the figure `五点 H0 单变量切片：不是全参数拟合`. Save deterministic SVG and 220-dpi PNG, with no raster image embedded in the SVG.

- [ ] **Step 3: Generate review.json and Markdown from one object**

`review.json` includes `schema`, `sources`, `source_lineage`, `directions`, `evidence`, `open_boundaries`, and `figure`. Set these explicit false boundaries:

```python
{
    "global_cosmological_fit_completed": False,
    "nonlinear_matter_spectrum_completed": False,
    "extreme_phase_sequence_converged": False,
    "accuracy_boost_8_completed": False,
    "physical_intuition_engine_validated": False,
}
```

`evidence.unit_tests` is exactly `{"passed": 41, "total": 41}` and carries the actual baseline command. `evidence.h0_scan` uses the summary values and exact minimum delta, never a rounded replacement.

The Markdown contains:

1. source hashes and one-lineage decision;
2. a four-row direction table with status and unfinished work;
3. fixed zero-model negative evidence and the native formula `Δχ² = χ²_zero − χ²_ΛCDM`;
4. the H0 table, then `![图 1：H0 单变量切片](h0-scan-comparison.svg)`, then its interpretation;
5. BBN, full-CMB, cross-code, and k800 boundaries;
6. the explicit sentence `物理直觉引擎尚未验证有效` and the boundary `不是整个无 CDM 模型族的排除`;
7. actual verification commands and scope limitations.

- [ ] **Step 4: Run the builder and independent source consistency check**

Run `python build_review.py`, then:

```bash
python -c "import json; r=json.load(open('review.json',encoding='utf-8')); h=json.load(open('C:/Users/一梦/Documents/kimi/workspace/.worktrees/provider-main-integration/research/physical-intuition/zero-cdm/planck-h0-scan-summary.json',encoding='utf-8')); assert r['evidence']['h0_scan']['minimum_delta_chi_squared']==h['decision']['minimum_delta_chi_squared']; assert r['evidence']['h0_scan']['expanded_scan_triggered']==h['decision']['expanded_scan_triggered']==False; print('h0_source_consistency=PASS')"
```

Expected: exit 0 and `h0_source_consistency=PASS`. Append output to `run.log`.

- [ ] **Step 5: Commit the evidence object, figure, and Markdown**

```bash
git add research/paper-direction-audit-2026-11-10/physical-intuition/build_review.py research/paper-direction-audit-2026-11-10/physical-intuition/review.json research/paper-direction-audit-2026-11-10/physical-intuition/h0-scan-comparison.svg research/paper-direction-audit-2026-11-10/physical-intuition/h0-scan-comparison.png research/paper-direction-audit-2026-11-10/physical-intuition/REVIEW.md research/paper-direction-audit-2026-11-10/physical-intuition/run.log
git commit -m "docs: audit physical intuition directions and unfinished work"
```

---

### Task 3: Native Word and Final QA

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/physical-intuition/build_report.js`
- Create: `research/paper-direction-audit-2026-11-10/physical-intuition/.gitignore`
- Generate: `REVIEW.docx` and `word-qa/report.json`

**Interfaces:**
- Consumes: `review.json` and `h0-scan-comparison.png` only.
- Produces: a native report with TOC, OMML, true tables, header, PAGE footer, and the H0 figure.

- [ ] **Step 1: Build the native DOCX with docx-js**

Use the same layout discipline as the completed critical-manifold report: CJK font chain, A4 margins, visible cached TOC plus real TOC field, header `TOE-SYLVA · 物理直觉方向审计`, PAGE-only footer, and `features.updateFields=true`.

Include a real four-row direction table, an H0 table with five rows, and native math using `MathSuperScript`/`MathSubScript` for `Δχ² = χ²_zero − χ²_ΛCDM`. Insert the PNG immediately after the H0 table with natural aspect ratio and caption `图 1 五点 H0 单变量切片；不是全参数拟合`. Add all open boundaries and actual test commands without claiming global completion.

`.gitignore` excludes `node_modules/`, `__pycache__/`, `word-qa/*.png`, and candidate/temp files.

- [ ] **Step 2: Build, validate, and run the complete contract**

```bash
python "{kimi-word}/scripts/docx.py" check-docx /absolute/path/scripts-or-report-dir
python "{kimi-word}/scripts/docx.py" build /absolute/path/build_report.js /absolute/path/REVIEW.docx
python test_physical_intuition_audit.py -v
```

Expected: OOXML validation passes and all six audit tests pass. Append outputs to `run.log`.

- [ ] **Step 3: Render and inspect every final page**

Run `docx.py render` once into `word-qa`. Read the contact sheet and every page, especially the direction table, native equation, H0 table/figure, and final open-boundary section. Record actual page count, all content-loss findings, per-page observations, and final DOCX hash in `word-qa/report.json`. Do not use LibreOffice or old QA.

- [ ] **Step 4: Commit Word and QA**

```bash
git add research/paper-direction-audit-2026-11-10/physical-intuition/build_report.js research/paper-direction-audit-2026-11-10/physical-intuition/REVIEW.docx research/paper-direction-audit-2026-11-10/physical-intuition/.gitignore research/paper-direction-audit-2026-11-10/physical-intuition/word-qa/report.json research/paper-direction-audit-2026-11-10/physical-intuition/run.log
git commit -m "docs: deliver physical intuition audit in native Word"
```

---

### Task 4: Final Regression and Branch Delivery

- [ ] **Step 1: Re-run all evidence checks**

```bash
python -m unittest discover -s "C:/Users/一梦/Documents/kimi/workspace/.worktrees/provider-main-integration/research/physical-intuition/zero-cdm/tests" -p "test*.py" -v
python test_physical_intuition_audit.py -v
python -m json.tool review.json
python "{kimi-word}/scripts/docx.py" validate /absolute/path/REVIEW.docx
git diff --check
```

Expected: 41/41 unit tests, six audit tests, valid JSON, OOXML `PASSED`, and no format errors. Append all commands, exit codes, and key outputs to `run.log`.

- [ ] **Step 2: Commit final evidence and push**

```bash
git add research/paper-direction-audit-2026-11-10/physical-intuition/run.log docs/superpowers/plans/2026-11-10-physical-intuition-direction-audit.md
git commit -m "test: record physical intuition audit verification"
git push -u origin audit/physical-intuition-directions
```

Confirm local and `ls-remote` hashes match. Preserve the worktree and do not merge other branches. Do not mark the broader repository audit complete.

## Plan Self-Review

- Both source identities and their uncommitted-provider boundary are explicit.
- One lineage and four direction families prevent document/section count inflation.
- Fixed zero-model negative evidence is preserved without a model-family exclusion.
- The physical-intuition engine remains explicitly unvalidated.
- All report formats share one evidence object and one H0 data source, with real RED, numerical, and OOXML checks; final-view rendering is attempted and its outcome disclosed.

## Execution Record — 2026-11-10

- Specification committed in `e1c66aa`, implementation plan in `1cc5322`, and RED/baseline evidence in `a51ba47`. The provider suite ran 41 tests successfully; the audit contract then failed because `review.json` was absent.
- Evidence object, H0 figure, and Markdown committed in `41a1e40`. Two source-path and font issues were corrected without changing evidence: the repeated `research/physical-intuition` prefix was removed, and axis units use `km/s/Mpc` to avoid a missing superscript-minus glyph. Independent source comparison returned `h0_source_consistency=PASS`.
- Native Word and QA committed in `0a50070`. All six audit contracts pass, and `REVIEW.docx` passed 21-part OOXML validation with SHA-256 `591b36b564c44874ba091fe8e7a12d7faeb9c9088d5dd598baa05542c9d2b978`.
- Final-view rendering returned exit 6 (`E_RENDER_FAILED: EPERM`) because of the temporary-directory permission failure. It was not retried and LibreOffice was not used. `word-qa/report.json` explicitly marks visual QA unavailable and no visual pass is claimed.
- Final regression reran all 41 provider tests, all six audit contracts, JSON parsing, OOXML validation, and `git diff --check`; every executed command exited 0. Full evidence is in `run.log`.
- This closes only the two-document direction audit. Nonlinear and full-parameter fitting, extreme-phase convergence, AccuracyBoost=8, the physical-intuition engine, and the remaining 663 unaudited documents outside this group remain open.
