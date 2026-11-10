# Strength Review Word Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` in the current session. Subagents are prohibited by the owner. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Synchronize all 17 K1a/K1b/K2 supplements into the audit DOCX and make regeneration preserve existing resolutions and supplements, while fixing the validator that currently reports 16/16 despite missing content.

**Architecture:** Two independent test suites separate Word-content failure from regeneration data loss. A minimal ID-keyed merge and suffix-preservation fix protects existing evidence. The final DOCX is rebuilt from the current Markdown into a new candidate by an offline docx-js renderer with the existing 9026 DXA table grid, validated, and only then substituted for the old file. Final delivery validation uses the new QA report, not the old 16-page evidence.

**Tech Stack:** Python 3.12 standard library, `unittest`, vendored docx-js 9.7.1 with native Math API, OOXML/OMML, `kimi-word` validation and doc-k final-view rendering.

## Global Constraints

- Work in `fix/strength-word-sync` under `C:\Users\一梦\Documents\kimi\workspace\.worktrees\strength-word-sync`.
- Do not alter the 55 baseline judgments, any Lean proof, other audit papers, or untracked historical QA/work directories.
- Never run the old base renderer in the actual audit directory during tests. Regeneration runs only in a temporary same-level directory under `research/`.
- Preserve every `resolution_2026_11_10` and extra summary field by paper ID, never by list position.
- Current supplement headings are exactly 17 in Markdown order. Reject duplicates or missing sections instead of silently repairing them.
- Do not claim whole-repository review, external novelty, mathematical proof, or K0(R) completion.
- Do not commit temporary baselines, unpacked DOCX files, QA page images, or temporary regeneration directories.

---

### Task 1: Word-Content and Regeneration RED Tests

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/test_strength_word_content.py`
- Create: `research/paper-direction-audit-2026-11-10/test_strength_regeneration_preserves.py`
- Create: `research/paper-direction-audit-2026-11-10/strength-word-sync-red.log`

**Interfaces:**
- Consumes: current `STRENGTH_SERIES_REVIEW.md`, current DOCX, current two JSON ledgers, and real `scripts/render_strength_review.py`.
- Produces: `supplement_headings()`, `docx_text()`, and two independently executable `run_all_tests()` suites.

- [ ] **Step 1: Write the Word-content test**

```python
import re
import sys
import unittest
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

AUDIT = Path(__file__).resolve().parent
MD = AUDIT / "STRENGTH_SERIES_REVIEW.md"
DOCX = AUDIT / "STRENGTH_SERIES_REVIEW.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def supplement_headings():
    return [
        line[3:].strip()
        for line in MD.read_text(encoding="utf-8").splitlines()
        if re.match(r"^## (K1a |K1b |K2 )", line)
    ]


def docx_text():
    with zipfile.ZipFile(DOCX) as package:
        root = ET.fromstring(package.read("word/document.xml"))
        body = root.find(W + "body")
        if body is not None:
            for content_control in list(body.findall(W + "sdt")):
                body.remove(content_control)
        paragraphs = []
        for paragraph in root.iter(W + "p"):
            paragraphs.append("".join(node.text or "" for node in paragraph.iter(W + "t")))
        return "\n".join(paragraphs)


class WordContentTests(unittest.TestCase):
    def test_markdown_has_exactly_17_supplements(self):
        headings = supplement_headings()
        self.assertEqual(len(headings), 17)
        self.assertEqual(len(set(headings)), 17)

    def test_docx_contains_every_supplement_in_order_without_duplicates(self):
        text = docx_text()
        headings = supplement_headings()
        missing = [heading for heading in headings if heading not in text]
        self.assertEqual(missing, [])
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(all(text.count(heading) == 1 for heading in headings))

    def test_final_range_class_and_60_regression_are_present(self):
        text = docx_text()
        self.assertIn("K2 商层像模同构类复核补记（2026-11-10）", text)
        self.assertIn("60/60", text)

    def test_native_ooxml_structure(self):
        with zipfile.ZipFile(DOCX) as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            headers = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footers = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
        self.assertIn(b"TOC", document)
        self.assertIn(b"<m:oMath", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 2)
        self.assertIn("55篇逐篇初审", headers.decode("utf-8"))
        self.assertIn(b"PAGE", footers)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
```

- [ ] **Step 2: Run Word-content RED and save all 17 missing headings**

Run: `python test_strength_word_content.py -v` from the audit directory.

Expected: exit 1. `test_docx_contains_every_supplement...` reports all 17 missing headings, and the final range-class check also fails. Native structure and Markdown-count tests may pass; do not mistake those for content synchronization. Save full output to `strength-word-sync-red.log`.

- [ ] **Step 3: Write the real regeneration test**

```python
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AUDIT = Path(__file__).resolve().parent


def workspace_root():
    for parent in AUDIT.parents:
        if (parent / "garden-ecosystem").is_dir() and (parent / "toe-sylva-audit").is_dir():
            return parent
    raise RuntimeError("cannot locate workspace containing garden-ecosystem and toe-sylva-audit")


RESEARCH = workspace_root() / "garden-ecosystem/research"
SCRIPT = AUDIT / "scripts/render_strength_review.py"
INPUTS = [
    "math-focus.json",
    "strength-review.json",
    "strength-review-summary.json",
    "STRENGTH_SERIES_REVIEW.md",
]
RECORD_BASELINE = {"id", "series", "title", "role", "novelty", "unfinished", "priority", "evidence", "source_line_1"}
SUMMARY_BASELINE = {"status", "reviewed", "series", "priorities", "unique_ids", "evidence_files_exist", "external_novelty_certified", "machine_proofs_certified_by_this_review"}


class RegenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before_records = json.loads((AUDIT / "strength-review.json").read_text(encoding="utf-8"))["records"]
        cls.before_summary = json.loads((AUDIT / "strength-review-summary.json").read_text(encoding="utf-8"))
        cls.before_md = (AUDIT / "STRENGTH_SERIES_REVIEW.md").read_text(encoding="utf-8")
        cls.temp = tempfile.TemporaryDirectory(prefix="strength-regeneration-", dir=RESEARCH)
        cls.copy = Path(cls.temp.name)
        (cls.copy / "scripts").mkdir()
        shutil.copy2(SCRIPT, cls.copy / "scripts/render_strength_review.py")
        for name in INPUTS:
            shutil.copy2(AUDIT / name, cls.copy / name)
        cls.completed = subprocess.run(
            [sys.executable, str(cls.copy / "scripts/render_strength_review.py")],
            cwd=cls.copy,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
        )
        if cls.completed.returncode != 0:
            raise RuntimeError(f"base renderer failed: {cls.completed.stdout}\n{cls.completed.stderr}")
        cls.after_records = json.loads((cls.copy / "strength-review.json").read_text(encoding="utf-8"))["records"]
        cls.after_summary = json.loads((cls.copy / "strength-review-summary.json").read_text(encoding="utf-8"))
        cls.after_md = (cls.copy / "STRENGTH_SERIES_REVIEW.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_resolution_fields_preserved_by_id(self):
        after_by_id = {record["id"]: record for record in self.after_records}
        losses = []
        for before in self.before_records:
            after = after_by_id.get(before["id"], {})
            for key, value in before.items():
                if key not in RECORD_BASELINE and after.get(key) != value:
                    losses.append((before["id"], key))
        self.assertEqual(losses, [])

    def test_summary_resolution_fields_preserved(self):
        losses = [key for key, value in self.before_summary.items() if key not in SUMMARY_BASELINE and self.after_summary.get(key) != value]
        self.assertEqual(losses, [])

    def test_supplements_preserved_in_order_without_duplicates(self):
        headings = [line[3:].strip() for line in self.before_md.splitlines() if line.startswith(("## K1a ", "## K1b ", "## K2 "))]
        self.assertEqual(len(headings), 17)
        self.assertTrue(all(self.after_md.count(heading) == 1 for heading in headings))
        positions = [self.after_md.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
```

- [ ] **Step 4: Run regeneration RED in the isolated copy**

Run: `python test_strength_regeneration_preserves.py -v`

Expected: exit 1 because resolution, summary extras, and all 17 supplements disappear in the temporary copy. The script itself must have run successfully and the actual audit files must remain byte-identical. Append full output and the actual audit-file hashes to `strength-word-sync-red.log`.

- [ ] **Step 5: Commit both failing suites and their evidence**

```bash
git add research/paper-direction-audit-2026-11-10/test_strength_word_content.py research/paper-direction-audit-2026-11-10/test_strength_regeneration_preserves.py research/paper-direction-audit-2026-11-10/strength-word-sync-red.log docs/superpowers/plans/2026-11-10-strength-review-word-sync.md
git commit -m "test: reproduce Word sync and regeneration data loss"
```

---

### Task 2: Minimal Preservation Fix

**Files:**
- Modify: `research/paper-direction-audit-2026-11-10/scripts/render_strength_review.py`
- Test: `research/paper-direction-audit-2026-11-10/test_strength_regeneration_preserves.py`

**Interfaces:**
- Consumes: both JSON ledgers and current Markdown before baseline generation.
- Produces: `merge_extras()`, `supplement_suffix()`, and preservation of all existing resolution/extra fields and supplement sections.

- [ ] **Step 1: Add ID-keyed record and summary merging**

Add these helpers and baseline key sets near the imports:

```python
RECORD_BASELINE_KEYS = {"id", "series", "title", "role", "novelty", "unfinished", "priority", "evidence", "source_line_1"}
SUMMARY_BASELINE_KEYS = {"status", "reviewed", "series", "priorities", "unique_ids", "evidence_files_exist", "external_novelty_certified", "machine_proofs_certified_by_this_review"}


def merge_extras(baseline, existing, baseline_keys):
    merged = dict(existing)
    for key in baseline_keys:
        merged[key] = baseline[key]
    return merged


def supplement_suffix(markdown):
    heading_lines = [
        line for line in markdown.splitlines()
        if re.match(r"^## (?:K1a |K1b |K2 )", line)
    ]
    if len(heading_lines) != len(set(heading_lines)):
        raise ValueError("duplicate K1a/K1b/K2 supplement heading")
    matches = list(re.finditer(r"(?m)^## (?:K1a |K1b |K2 )", markdown))
    if not matches:
        return ""
    return markdown[matches[0].start():].rstrip() + "\n"
```

Before writing `strength-review.json`, load any existing records by ID and merge each new baseline record with the existing record of the same ID. If an old record carrying extras has no new ID, raise `ValueError` instead of dropping it:

```python
review_path = AUDIT / "strength-review.json"
previous = json.loads(review_path.read_text(encoding="utf-8"))["records"] if review_path.exists() else []
previous_by_id = {record["id"]: record for record in previous}
new_ids = {record["id"] for record in records}
for old in previous:
    if old["id"] not in new_ids and any(key not in RECORD_BASELINE_KEYS for key in old):
        raise ValueError(f"baseline would remove extended record: {old['id']}")
records = [merge_extras(record, previous_by_id.get(record["id"], {}), RECORD_BASELINE_KEYS) for record in records]
review_path.write_text(json.dumps({"status": "initial_review_not_external_certification", "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
```

Before writing `strength-review-summary.json`, load the existing summary if present and use the same baseline-key refresh:

```python
summary_path = AUDIT / "strength-review-summary.json"
previous_summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
summary = merge_extras(summary, previous_summary, SUMMARY_BASELINE_KEYS)
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
```

- [ ] **Step 2: Preserve the supplement suffix without changing baseline prose**

Before `(AUDIT / "STRENGTH_SERIES_REVIEW.md").write_text(...)`, replace direct writing with:

```python
review_md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
existing_md = review_md_path.read_text(encoding="utf-8") if review_md_path.exists() else ""
suffix = supplement_suffix(existing_md)
baseline_md = "\n".join(lines).rstrip() + "\n"
final_md = baseline_md if not suffix else baseline_md + "\n" + suffix
review_md_path.write_text(final_md, encoding="utf-8", newline="\n")
```

This preserves the exact existing suffix, including body text, links, and order. It does not infer new scientific content.

- [ ] **Step 3: Run regeneration GREEN and confirm the actual audit was untouched**

Run: `python test_strength_regeneration_preserves.py -v`

Expected: exit 0, three tests pass. Verify actual `strength-review.json`, `strength-review-summary.json`, and `STRENGTH_SERIES_REVIEW.md` hashes equal the pre-test values. Save the output in `strength-word-sync-green.log`.

- [ ] **Step 4: Commit the minimal preservation fix**

```bash
git add research/paper-direction-audit-2026-11-10/scripts/render_strength_review.py research/paper-direction-audit-2026-11-10/strength-word-sync-green.log
git commit -m "fix: preserve resolutions during strength regeneration"
```

---

### Task 3: Rebuild DOCX and Repair Delivery Validation

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/scripts/build_strength_review_docx.js`
- Modify: `research/paper-direction-audit-2026-11-10/scripts/verify_strength_delivery.py`
- Create: `research/paper-direction-audit-2026-11-10/.gitignore`
- Replace after candidate validation: `STRENGTH_SERIES_REVIEW.docx`

**Interfaces:**
- Consumes: current Markdown, current DOCX as read-only backup, and current status PNG.
- Produces: candidate DOCX with all supplements, stable table widths, Chinese header, PAGE footer, native TOC and OMML.

- [ ] **Step 1: Implement the offline docx-js candidate builder**

Create `.gitignore` with `/strength-word-sync-work/`, `/strength-word-sync-qa/*.png`, and `node_modules/`. Create `scripts/build_strength_review_docx.js`; it copies the current DOCX to `strength-word-sync-work/baseline.docx` and writes only `STRENGTH_SERIES_REVIEW.candidate.docx` before validation.

Pandoc was searched for and is unavailable, so the builder uses the vendored docx-js 9.7.1 package and no installation. Its bounded Markdown renderer implements these exact mappings:

- `#`, `##`, `###` become native TITLE/HEADING_1/HEADING_2 paragraphs; every level-2 title is also included in a visible cached TOC with a real `TOC \o "1-2" \h \z \u` field and `features.updateFields=true`.
- Consecutive `|` lines become real tables. The separator row is skipped. The two six-column tables use `columnWidths=[420,1350,1250,1700,3506,800]`, a 9026 DXA table width, matching per-cell widths, 7-point table text, and a repeated header row.
- `[label](target)` becomes `ExternalHyperlink`; Windows targets are converted to `file:///C:/...` URLs. `**bold**` and backtick code become styled `TextRun` children, not literal markup.
- `![alt](strength-review-status.png)` becomes an `ImageRun` with `type:"png"`; PNG width/height are read from bytes 16 and 20 and height is derived from the natural aspect ratio.
- `- ` and numbered lines use docx-js `numbering` references, never typed bullet characters. Blockquotes become shaded note paragraphs and `---` becomes a bottom-border separator.
- The only display formula, `ψ_toy''(μ)=1 ⇒ 1/(ψ_toy''(μ))=1, μ∈ℝ`, is built with `MathSubScript`, `MathSuperScript`, `MathFraction`, and `MathRun`, including nested scripts and a true fraction. No formula screenshot or raw LaTeX is used.

The formula helper is exactly:

```javascript
const psiToyPrime = () => new MathSuperScript({
  children: [new MathSubScript({ children: [new MathRun("ψ")], subScript: [new MathRun("toy")] })],
  superScript: [new MathRun("′′")],
});
const nativeFormula = () => para(new MathEquation({ children: [
  psiToyPrime(), new MathRun("(μ) = 1   ⇒   "),
  new MathFraction({ numerator: [new MathRun("1")], denominator: [psiToyPrime(), new MathRun("(μ)")] }),
  new MathRun(" = 1,   μ ∈ ℝ"),
] }), { alignment: AlignmentType.CENTER });
```

The Document uses A4, 1440 DXA margins, the existing CJK font chain, Chinese header `TOE-SYLVA · 55篇逐篇初审 · 证据边界与补记`, current-page-only footer, and `Packer.toBuffer`. `main()` parses the 256 Markdown lines in order and never invents supplement prose.

- [ ] **Step 2: Build and validate the candidate without replacing the baseline**

Run `docx.py check-docx` for the script directory, then:

```bash
python "{kimi-word}/scripts/docx.py" build /absolute/path/build_strength_review_docx.js /absolute/path/STRENGTH_SERIES_REVIEW.candidate.docx
python "{kimi-word}/scripts/docx.py" validate /absolute/path/STRENGTH_SERIES_REVIEW.candidate.docx
```

Expected: candidate exists and both gates exit 0 with no document warning left unaddressed. Any violation stops before replacement. Do not use LibreOffice or install Pandoc.

- [ ] **Step 3: Replace the old DOCX and run content GREEN**

Only after candidate validation passes, replace `STRENGTH_SERIES_REVIEW.docx` with the candidate and run:

```bash
python test_strength_word_content.py -v
```

Expected: exit 0, four tests pass; all 17 headings occur once and in Markdown order, with final range-class and `60/60` present. Save output to `strength-word-sync-green.log`.

- [ ] **Step 4: Add content checks to the old 16-check validator**

Change the QA input to `strength-word-sync-qa/report.json`. Import `supplement_headings` and `docx_text` from `test_strength_word_content`, then add:

```python
    text = docx_text()
    headings = supplement_headings()
    check("Markdown补记数", len(headings), 17)
    check("DOCX缺失补记", [heading for heading in headings if heading not in text], [])
    check("补记重复项", [heading for heading in headings if text.count(heading) != 1], [])
    check("商层与60项回归", "K2 商层像模同构类复核补记（2026-11-10）" in text and "60/60" in text, True)
    check("逐页人工复核记录", qa.get("manualReview", {}).get("reviewedPages"), list(range(1, qa["pages"] + 1)))
```

The final validator must contain 21 checks. Before DOCX replacement it must fail missing content instead of reporting 16/16; after replacement and current QA it must report 21/21 only when the content and QA are both current.

- [ ] **Step 5: Commit the synchronized document and stronger validator**

```bash
git add research/paper-direction-audit-2026-11-10/STRENGTH_SERIES_REVIEW.docx research/paper-direction-audit-2026-11-10/scripts/build_strength_review_docx.js research/paper-direction-audit-2026-11-10/scripts/verify_strength_delivery.py research/paper-direction-audit-2026-11-10/.gitignore research/paper-direction-audit-2026-11-10/strength-word-sync-green.log
git commit -m "fix: synchronize all strength supplements into Word"
```

---

### Task 4: Final View, 21/21 Validation, and Branch Delivery

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/strength-word-sync-qa/report.json`
- Create: `research/paper-direction-audit-2026-11-10/strength-word-sync-final.log`

- [ ] **Step 1: Validate and render the final DOCX once**

Run `docx.py validate` on the final path, then `docx.py render` into `strength-word-sync-qa`. Read `contact-sheet.png` first and then every page, every near-blank page, and every `content-loss` finding. Never use LibreOffice. If rendering is unavailable, disclose exit 4/5/6 without retry and do not call it a visual pass.

- [ ] **Step 2: Record real page observations in QA JSON**

Add `manualReview` with `contactSheetRead: true`, `reviewedPages: [1, ..., pages]`, page-specific observations, clipped/blank-page findings, and content-loss interpretation. Record the final DOCX SHA-256, validator command/exit code, render command/exit code, and actual page count. QA page PNGs remain ignored.

- [ ] **Step 3: Run all final checks and write the full log**

```bash
python test_strength_word_content.py -v
python test_strength_regeneration_preserves.py -v
python scripts/verify_strength_delivery.py
python "{kimi-word}/scripts/docx.py" validate /absolute/path/STRENGTH_SERIES_REVIEW.docx
git diff --check
```

Expected: 4/4 content tests, 3/3 regeneration tests, 21/21 delivery checks, OOXML `PASSED`, and no format errors. Save actual commands, exit codes, key outputs, and RED/GREEN lineage to `strength-word-sync-final.log`.

- [ ] **Step 4: Commit final evidence and push the named branch**

```bash
git add research/paper-direction-audit-2026-11-10/strength-word-sync-qa/report.json research/paper-direction-audit-2026-11-10/strength-word-sync-final.log research/paper-direction-audit-2026-11-10/strength-delivery-validation.json docs/superpowers/plans/2026-11-10-strength-review-word-sync.md
git commit -m "test: verify strength Word synchronization"
git push -u origin fix/strength-word-sync
```

Confirm `git rev-parse HEAD` and `git ls-remote origin refs/heads/fix/strength-word-sync` match. Preserve the worktree; do not merge `research/paper-direction-atlas` or `main`.

## Plan Self-Review

- The two RED classes are independent: missing DOCX content and regeneration data loss.
- Record merging is ID-keyed; baseline fields refresh while all extra fields survive.
- Supplement suffix preservation is exact and duplicate-rejecting, with no scientific rewriting.
- The old validator cannot report success without all 17 headings and current manual QA.
- Final Word validation and visual review apply to the rebuilt file, not the historical 16-page artifact.
