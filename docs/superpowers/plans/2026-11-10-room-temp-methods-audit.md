# Room Temperature SC Methods Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` in the current session. Subagents are prohibited by the owner. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Deliver an evidence-gated audit of five room_temp_sc method/formalization documents and one Lean asset, separating one research lineage, five method directions, verified corrections, proof debt, templates, and unfinished work.

**Architecture:** A Python builder resolves the read-only `toe-sylva-audit` sources, verifies six frozen hashes, extracts proof/template debt, and writes one `review.json`. The same object drives `REVIEW.md` and a docx-js `REVIEW.docx`. A standalone unittest contract fails before the evidence object exists and then checks all report formats and negative boundaries.

**Tech Stack:** Python 3 standard library, unittest, local extracted primary-source text, APS/PNAS official source records, Node ≥18 with vendored docx-js, native OMML through the docx Math API, `kimi-word` OOXML validation and doc-k final-view rendering.

## Global Constraints

- Work in `research/paper-direction-audit-2026-11-10/room-temp-methods/`, the specification, and this plan only; keep all six source files read-only.
- Use the six SHA-256 values in `docs/superpowers/specs/2026-11-10-room-temp-methods-audit-design.md`; abort on source drift.
- `research_program_count=1`; use five method-direction IDs, not five new theories.
- Preserve the verified mappings `220 GPa→320 K`, `250 GPa→322 K`; DOS-scaling `285/301 K` is a lower bound, not an accurate point prediction.
- DMRG is `PRL 133, 256003`; LaSc₂H₂₄ is `PNAS 121(26)` and a theoretical prediction, not an experimental record.
- Do not confuse sharp constant `0.1827262477…` with the non-optimal upper-bound coefficient `2.034×` larger.
- Lean remains a draft; SI remains a template. Do not run or claim Lean compilation, new proofs, material predictions, or global fits.
- Do not add `axiom`, `postulate`, proof-hole `sorry`, or vacuous theorems. Do not modify provider worktrees or unrelated untracked files.
- Run doc-k render once; exit 4/5/6 means visual QA unavailable, with no retry and no LibreOffice fallback.

---

### Task 1: Frozen specification and missing-evidence RED

**Files:**
- Create: `docs/superpowers/specs/2026-11-10-room-temp-methods-audit-design.md`
- Create: `research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py`
- Create: `research/paper-direction-audit-2026-11-10/room-temp-methods/run.log`

**Interfaces:**
- Consumes: future `review.json`, `REVIEW.md`, and `REVIEW.docx`.
- Produces: `run_all_tests() -> int` and ten independent audit contracts.

- [ ] **Step 1: Write the failing test before the evidence object exists**

Use this exact test skeleton, with all six expected hashes copied from the specification:

```python
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "latest_digest": "41aea15ed19c68375f29877f7e22deba22394757df178cb67ca827a458a0aa75",
    "floquet_notes": "37b5436dc39bada84c3a520943ea94515d5d08e75c27e808aba5070059d48ab9",
    "eliashberg_notes": "841c1954c7fea9c41e3179476602c64b47eca936643f383e24215284324d0a20",
    "lean_markdown": "c171f6e5d5e5b6547bddc88d94138b9dc0a87d8c3a6ec59ff696e35746f59141",
    "si_template": "9d54064ba6089c82de39ddef90afeb82e47d511f95b35dd0490ee50aef63d97f",
    "lean_standalone": "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439",
}

class RoomTempMethodsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_hashes(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 5)
        self.assertEqual({r["id"]: r["sha256"] for r in self.data["sources"]}, EXPECTED_HASHES)

    def test_floquet_pressure_mapping(self):
        rows = self.data["evidence"]["floquet"]["dfpt_estimates"]
        self.assertEqual({r["pressure_gpa"]: r["driven_tc_k"] for r in rows}, {220: 320, 250: 322})

    def test_dos_scaling_is_lower_bound(self):
        rows = self.data["evidence"]["floquet"]["dos_scaling_estimates"]
        self.assertEqual({r["pressure_gpa"]: r["driven_tc_k"] for r in rows}, {150: 285, 200: 301})
        self.assertTrue(all(r["role"] == "lower_bound_not_accurate_prediction" for r in rows))

    def test_dmrg_bibliography_and_scope(self):
        row = self.data["evidence"]["dmrg"]
        self.assertEqual((row["volume"], row["article"]), (133, "256003"))
        self.assertEqual(row["max_cylinder_width"], 6)
        self.assertAlmostEqual(row["max_characteristic_tc_star_over_j"], 0.15)

    def test_lasch24_is_prediction_and_issue_26(self):
        row = self.data["evidence"]["lasc2h24"]
        self.assertEqual(row["issue"], 26)
        self.assertTrue(row["theoretical_prediction"])
        self.assertFalse(row["experimental_confirmation"])

    def test_kiessling_constant_roles(self):
        row = self.data["evidence"]["eliashberg"]
        self.assertAlmostEqual(row["sharp_constant"], 0.1827262477)
        self.assertAlmostEqual(row["upper_bound_multiplier"], 2.034)
        self.assertAlmostEqual(row["upper_bound_coefficient"], row["sharp_constant"] * 2.034)
        self.assertNotEqual(row["upper_bound_coefficient"], row["sharp_constant"])

    def test_lean_is_unverified_draft(self):
        row = self.data["evidence"]["lean"]
        self.assertEqual(row["status"], "draft_not_machine_verified")
        self.assertFalse(row["build_attempted"])
        self.assertFalse(row["build_passed"])
        self.assertGreater(row["markdown_proof_hole_count"], 0)
        self.assertEqual(set(row["standalone_sorry_theorems"]), {"allenDynes_weak_coupling_limit", "bcs_isotope_effect", "floquet_enhanced_tc"})

    def test_si_is_template_and_negative_boundaries(self):
        self.assertEqual(self.data["evidence"]["si"]["status"], "template_only")
        self.assertGreater(self.data["evidence"]["si"]["placeholder_count"], 0)
        for key in ("global_fit", "material_prediction", "lean_proof_verified", "dft_inputs_available", "phonon_spectra_available", "full_repository_audit_completed"):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_unverified_and_out_of_scope_findings_are_registered(self):
        self.assertEqual(self.data["evidence"]["external_lean_metrics"]["status"], "unverified")
        self.assertGreaterEqual(len(self.data["out_of_scope_findings"]), 3)

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("220 GPa → 320 K", "250 GPa → 322 K", "草案，不是机器证明", "模板，不是已完成的补充信息", "全库审计尚未完成"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            document = package.read("word/document.xml")
            names = package.namelist()
            header = b"".join(package.read(n) for n in names if n.startswith("word/header") and n.endswith(".xml"))
            footer = b"".join(package.read(n) for n in names if n.startswith("word/footer") and n.endswith(".xml"))
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 4)
        self.assertIn(b"PAGE", footer)
        self.assertIn("室温超导", header.decode("utf-8"))

def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(run_all_tests())
```

- [ ] **Step 2: Run and record the intentional RED**

```bash
cd C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit
python research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py -v
```

Expected: exit 1 with `FileNotFoundError: review.json`. Record the full command, exit code, and unfiltered failure in `run.log`.

- [ ] **Step 3: Commit the specification and failing contract**

```bash
git add docs/superpowers/specs/2026-11-10-room-temp-methods-audit-design.md docs/superpowers/plans/2026-11-10-room-temp-methods-audit.md research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py research/paper-direction-audit-2026-11-10/room-temp-methods/run.log
git commit -m "test: define room temperature methods audit contracts"
```

---

### Task 2: One evidence object and Markdown report

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/room-temp-methods/build_review.py`
- Generate: `review.json`, `REVIEW.md`

**Interfaces:**
- `find_source_root(start: Path) -> Path`: locate `toe-sylva-audit/papers/room_temp_sc` without modifying it.
- `build_data() -> dict`: return the sole evidence object.
- `build_markdown(data: dict) -> str`: render the same object without independent numerical constants.
- `main() -> None`: write deterministic UTF-8 JSON and Markdown.

- [ ] **Step 1: Implement source and debt extraction**

Use `SOURCE_PATHS` mapping the six IDs to the exact relative paths in the specification. For each file compute SHA-256 and compare to `EXPECTED_HASHES`; raise `ValueError` on drift. Count Markdown proof holes with `re.findall(r"(?m)^\s*(?:admit|sorry)\b", text)` and SI placeholders with case-insensitive occurrences of `to be imported`, `to be specified`, `待补充`, `placeholder`, and bracketed software/repository markers. Extract the three theorem names by finding each `theorem <name>` followed before the next theorem/end by a line containing only `sorry`.

Do not execute Lean. Record:

```python
{
    "status": "draft_not_machine_verified",
    "build_attempted": False,
    "build_passed": False,
    "standalone_sorry_theorems": [
        "allenDynes_weak_coupling_limit",
        "bcs_isotope_effect",
        "floquet_enhanced_tc",
    ],
}
```

- [ ] **Step 2: Encode primary-source facts once**

`evidence.floquet.dfpt_estimates` contains exactly:

```python
[
    {"pressure_gpa": 220, "equilibrium_tc_k": 258, "driven_tc_k": 320, "field_mv_per_angstrom": 80, "role": "direct_floquet_dfpt_allen_dynes_estimate"},
    {"pressure_gpa": 250, "equilibrium_tc_k": 237, "driven_tc_k": 322, "field_mv_per_angstrom": 80, "role": "direct_floquet_dfpt_allen_dynes_estimate"},
]
```

`dos_scaling_estimates` contains 150:249→285 and 200:240→301 with `role="lower_bound_not_accurate_prediction"`. Add `not_all_hydrides_above_room_temperature=True` and local source line locators 421–428, 556–584, 591–594.

Encode DMRG volume 133/article 256003/date 2024-12-19/width 6/minimum T/J 0.06/maximum characteristic 0.15J and opposite t′ behavior. Encode LaSc₂H₂₄ issue 26/article e2401840121, 167 GPa→316 K, 250 GPa→331 K, anharmonic dynamical stability to 150 GPa, `theoretical_prediction=True`, `experimental_confirmation=False`.

Encode `sharp_constant=0.1827262477`, `upper_bound_multiplier=2.034`, and compute `upper_bound_coefficient=sharp_constant*upper_bound_multiplier`. External Lean metrics use `status="unverified"`; SI uses `status="template_only"`.

- [ ] **Step 3: Generate the Markdown from the evidence object**

Use five direction records with IDs `floquet_evidence`, `eliashberg_bounds`, `lean_formalization`, `literature_digest`, `reproducible_si`. Include source hashes, a correction table, the Floquet table, DMRG/LaSc₂H₂₄ scope, native Markdown formula `C_upper = 2.034 C_sharp ≈ 0.371665`, Lean and SI debt, range-out findings, prioritized next actions, and actual verification scope.

The report must contain the exact contract phrases `220 GPa → 320 K`, `250 GPa → 322 K`, `草案，不是机器证明`, `模板，不是已完成的补充信息`, and `全库审计尚未完成`. Unverified claims are not called false; corrections are not called new scientific results.

- [ ] **Step 4: Run the builder and independent consistency checks**

```bash
python research/paper-direction-audit-2026-11-10/room-temp-methods/build_review.py
python research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py -v
```

Expected after this task: numerical/JSON tests pass; only the Markdown/Word test may fail because `REVIEW.docx` does not yet exist. Independently parse local Xie lines 421–428 and assert `220` is adjacent to `320`, `250` to `322`; assert JSON values match the official APS/PNAS records. Append actual outputs and exit codes to `run.log`.

---

### Task 3: Native Word report

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/room-temp-methods/build_report.js`
- Create: `research/paper-direction-audit-2026-11-10/room-temp-methods/.gitignore`
- Generate: `REVIEW.docx`, `word-qa/report.json`

**Interfaces:**
- Consumes only `review.json` in the report directory.
- Produces a native Word report with visible cached TOC plus TOC field, CJK header, PAGE footer, at least four true tables, and one native Math equation.

- [ ] **Step 1: Implement the docx-js renderer**

Read `review.json` from `path.dirname(process.argv[2])`. Use explicit font channels `Times New Roman` and `SimSun`, A4 margins 1200 DXA, stable DXA table/cell widths, `ShadingType.CLEAR`, `HeadingLevel.HEADING_1/2`, `features.updateFields=true`, and the `ImportedXmlComponent` cached-TOC pattern from `kimi-word`.

Create tables for source lineage, corrections, Floquet values, five directions, and out-of-scope findings. Create the native equation with `MathRun` nodes in visible order:

```js
const constantEquation = () => para(new MathEquation({ children: [
  new MathRun("C"),
  new MathSubScript({ children: [], subScript: [new MathRun("upper")] }),
  new MathRun(" = 2.034 "),
  new MathRun("C"),
  new MathSubScript({ children: [], subScript: [new MathRun("sharp")] }),
  new MathRun(" ≈ 0.371665"),
] }), { alignment: AlignmentType.CENTER });
```

Use the actual docx Math API signature if the vendored version requires a nonempty base; preserve native `m:oMath` output. Do not render the equation as an image or plain slash notation. `.gitignore` excludes `node_modules/`, `__pycache__/`, `word-qa/*.png`, and temporary candidate files.

- [ ] **Step 2: Build and validate through the required entry point**

```bash
PATH="/c/Program Files/nodejs:$PATH" python "C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py" check-docx "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods"
PATH="/c/Program Files/nodejs:$PATH" python "C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py" build "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods/build_report.js" "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.docx"
```

Expected: both exit 0 and OOXML `PASSED`. Do not pipe build output through filters.

- [ ] **Step 3: Run all contracts and render once**

```bash
python research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py -v
PATH="/c/Program Files/nodejs:$PATH" python "C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py" render "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.docx" "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods/word-qa"
```

Expected: ten tests pass. If render exits 0, read `contact-sheet.png` first, then every page and all content-loss/near-blank findings; record page observations and final DOCX SHA-256 in `word-qa/report.json`. If it exits 4/5/6, stop rendering and record visual QA as unavailable with the exact error and exit code.

---

### Task 4: Final verification and branch delivery

- [ ] **Step 1: Re-run every final check**

```bash
python research/paper-direction-audit-2026-11-10/room-temp-methods/test_room_temp_methods_audit.py -v
python -m json.tool research/paper-direction-audit-2026-11-10/room-temp-methods/review.json
PATH="/c/Program Files/nodejs:$PATH" python "C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/docx.py" validate "C:/Users/一梦/Documents/kimi/workspace/.worktrees/room-temp-methods-audit/research/paper-direction-audit-2026-11-10/room-temp-methods/REVIEW.docx"
git diff --check
```

Expected: exit 0 for each, ten tests pass, JSON parses, OOXML passes, and no whitespace errors. Save commands, exit codes, and key outputs to `run.log`; do not reuse earlier audits as current evidence.

- [ ] **Step 2: Commit only audited artifacts and push the named branch**

```bash
git add docs/superpowers/plans/2026-11-10-room-temp-methods-audit.md research/paper-direction-audit-2026-11-10/room-temp-methods
git commit -m "docs: audit room temperature methods and unfinished work"
git push -u origin audit/room-temp-methods-batch
git rev-parse HEAD
git ls-remote origin refs/heads/audit/room-temp-methods-batch
```

Expected: remote and local full hashes match. Preserve the isolated worktree and do not merge. Close only this five-document method batch; leave the remaining room_temp_sc and repository audit open.

## Plan Self-Review

- All five required direction families, six frozen source assets, and one-lineage accounting are covered.
- Every numerical correction has an independent primary-source role and a failing-first contract.
- Unverified literature metrics and out-of-scope high-risk findings are registered without being called false.
- Lean compilation, global fitting, material prediction, DFT inputs, and full-repository completion remain explicitly negative.
- Markdown and Word share one JSON object; native TOC, tables, header, page number, and math are independently checked.
- Final-view rendering has a bounded single attempt and an honest unavailable path.
