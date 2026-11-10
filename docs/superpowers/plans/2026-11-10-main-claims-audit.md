# Main Claims and Handbook Evidence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` in the current session. Subagents are prohibited by the owner. Steps use checkbox (`- [ ]`) tracking.

**Goal:** Produce an evidence-gated audit of four manuscript versions and two handbook chapters, preserving both positive and negative LaSc₂H₂₄ experimental evidence while correcting a confirmed Nature citation mismatch and unsupported necessity/proof wording.

**Architecture:** A Python builder verifies ten frozen assets, reads the critical-manifold and previous-method JSON evidence, and emits one `review.json`. The same object drives a timeline figure and `REVIEW.md`; docx-js consumes the object and PNG to produce a native Word report. Independent tests check source text, Crossref metadata, numerical counterexamples, report contracts, and negative boundaries.

**Tech Stack:** Python 3 standard library, unittest, Matplotlib, pypdf extraction, arXiv primary PDFs, Crossref metadata, vendored docx-js 9.7.1, native OMML, `kimi-word` OOXML validation and doc-k final-view rendering.

## Global Constraints

- Work only in `research/paper-direction-audit-2026-11-10/main-claims/` and the specification/plan; keep six source documents and two evidence worktrees read-only.
- Use every SHA-256 in the specification; abort on drift. `research_program_count=1`, with four method directions, not four new theories.
- Preserve both Song's positive preprint and Semenok's negative preprint. Neither selective deletion nor a vote-count verdict is allowed.
- PNAS 2024 is a prediction; Song 2025 is an author-reported experiment; Semenok 2026 is an independent negative replication attempt. Peer review and independent positive replication remain unestablished.
- Nature 626, 779–784 is the boron-nitride ceramic article, not LaSc₂H₂₄. Do not backfill Song into a 2024 Nature citation.
- Numerical counterexamples apply only to the simplified formula and broad necessity wording, not all Eliashberg theory or materials.
- Unverified anecdotes are not called fabricated. Do not add axioms, postulates, proof-hole sorry, material predictions, or global fits.
- Run doc-k render once; no retry on exit 4/5/6 and no LibreOffice.

---

### Task 1: Missing-evidence RED

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/main-claims/test_main_claims_audit.py`
- Create: `research/paper-direction-audit-2026-11-10/main-claims/run.log`

**Interfaces:** future `review.json`, `REVIEW.md`, `REVIEW.docx`; `run_all_tests() -> int`.

- [ ] **Step 1: Write contract tests before the report exists**

Create tests for these exact behaviors:

```python
def test_song_positive_preprint_scope(self):
    row = self.data["evidence"]["song"]
    self.assertTrue(row["exists"])
    self.assertTrue(row["reports_experimental_synthesis"])
    self.assertEqual(row["onset_tc_k"], [271, 298])
    self.assertEqual(row["pressure_gpa"], [195, 266])
    self.assertEqual(row["reproducible_runs_reported"], 13)
    self.assertFalse(row["peer_review_established"])
    self.assertFalse(row["independent_positive_replication"])
    self.assertFalse(row["direct_meissner_completed"])

def test_semenok_negative_replication_scope(self):
    row = self.data["evidence"]["semenok"]
    self.assertTrue(row["exists"])
    self.assertEqual(row["unsuccessful_attempts"], 7)
    self.assertEqual(row["synthesis_pressure_gpa"], [250, 280])
    self.assertEqual(row["no_superconductivity_range_k"], [245, 300])
    self.assertTrue(row["theoretical_tc_above_300_at_300_gpa"])

def test_confirmed_nature_citation_mismatch(self):
    row = self.data["evidence"]["nature_citation"]
    self.assertTrue(row["citation_mismatch"])
    self.assertEqual(row["actual_title"], "Twisted-layer boron nitride ceramic with high deformability and strength")
    self.assertEqual(row["actual_doi"], "10.1038/s41586-024-07036-5")

def test_counterexample_and_negative_boundaries(self):
    critical = self.data["evidence"]["critical_manifold"]
    self.assertEqual(critical["root_count"], 936)
    self.assertEqual(critical["grid_point_count"], 38376)
    self.assertEqual(critical["grid_class_disagreements"], 0)
    self.assertTrue(all(row["tc_K"] < 300 for row in critical["temperature_anchors"]))
    for key in ("formal_proof_completed", "lean_proof_verified", "si_complete", "peer_review_established", "independent_positive_replication", "direct_meissner_completed", "success_rate_100_supported", "ultimate_necessity_proven", "full_repository_audit_completed"):
        self.assertFalse(self.data["open_boundaries"][key])
```

Add tests for ten source hashes, one lineage/four directions, `contested_evidence=True`, `success_rate_100_supported=False`, `anecdote_status="unverified"`, `prior_audit_addendum_required=True`, and Markdown/Word structure. The Word contract must find native `m:oMath`, TOC, at least four tables, PAGE, a media image, five primary-source footnotes, and Chinese header text.

- [ ] **Step 2: Run intentional RED**

```bash
python research/paper-direction-audit-2026-11-10/main-claims/test_main_claims_audit.py -v
```

Expected: exit 1 with `FileNotFoundError: review.json`; record the full failure in `run.log`.

- [ ] **Step 3: Commit the specification and failing contract**

```bash
git add docs/superpowers/specs/2026-11-10-main-claims-audit-design.md docs/superpowers/plans/2026-11-10-main-claims-audit.md research/paper-direction-audit-2026-11-10/main-claims/test_main_claims_audit.py research/paper-direction-audit-2026-11-10/main-claims/run.log
git commit -m "test: define manuscript claims audit contracts"
```

---

### Task 2: Evidence object, source verification, timeline, and Markdown

**Files:**
- Create: `build_review.py`, `verify_primary_sources.py`, `sources/primary-source-excerpts.md`
- Generate: `review.json`, `claims-timeline.svg`, `claims-timeline.png`, `REVIEW.md`

**Interfaces:**
- `build_data() -> dict`: sole evidence object.
- `build_figure(data) -> None`: timeline from evidence records.
- `build_markdown(data) -> str`: same data, no separate fact database.
- `verify_primary_sources.run_all_tests() -> int`: independent primary-source checks.

- [ ] **Step 1: Implement frozen evidence resolution**

Resolve the six documents under `toe-sylva-audit/papers/room_temp_sc/`, critical results under `.worktrees/critical-manifold/`, and prior review under `room-temp-methods/`. Verify all ten hashes. Read three temperature anchors, 936 roots, 38,376 direct points and zero class disagreements from critical results; read 48 Markdown proof holes, 3 standalone sorry theorems and 31 SI placeholders from the previous review. Do not rerun Lean or the numerical pipeline.

- [ ] **Step 2: Encode primary-source records and boundaries**

Song: exists, experimental report, 271–298 K, 195–266 GPa, 13 reported runs, no established peer review/positive independent replication/direct Meissner. Semenok: exists, 7 unsuccessful attempts, 250–280 GPa, no SC at 245–300 K, precursor caveat and theoretical >300 K at 300 GPa. Nature citation: actual DOI/title/pages and `citation_mismatch=True`.

Set `contested_evidence=True`, `success_rate_100_supported=False`, `anecdote_status="unverified"`, `prior_audit_addendum_required=True`. Set all nine open boundaries in the specification to false.

- [ ] **Step 3: Build timeline and Markdown**

Use four events: PNAS prediction (2024), incorrect Nature citation (2024, bibliographic mismatch), Song positive preprint (2025), Semenok negative replication preprint (2026). Title the figure `理论预测、实验宣称与独立负向复现：不是真伪投票`. Save deterministic SVG and 220-dpi PNG. The Markdown inserts the figure after the evidence table and before the controversy interpretation, and states the exact insertion order.

Include the counterexample formula and three temperatures, Lean/SI debt, Nature mismatch, unverified anecdotes, prior-audit addendum, and a P0/P1/P2 correction plan. Do not call Song confirmed or Semenok fraudulent; do not generalize the simplified-formula counterexample.

- [ ] **Step 4: Verify independent source consistency**

Save exact Crossref title/DOI/page metadata and key source locators in `sources/primary-source-excerpts.md`. In `verify_primary_sources.py`, read the extracted Song and Semenok text and assert:

- Song contains `Through thirteen reproducible experimental runs`, `271-298 kelvin at 195-266 GPa`, and the future-Meissner passage;
- Semenok contains `Seven experimental attempts`, `unsuccessful`, and `245-300 K`;
- no `42nd`, `43rd`, `success rate`, or `million RMB` support is found for the anecdote;
- Crossref excerpt has the actual boron-nitride title and DOI;
- critical anchor temperatures and counts match `review.json`.

Run both scripts. Expected: builder exit 0; independent source tests all pass; main contract may fail only because DOCX is absent. Record actual outputs.

---

### Task 3: Native Word with figure and primary-source footnotes

**Files:**
- Create: `build_report.js`, `.gitignore`, `.gitattributes`
- Generate: `REVIEW.docx`, `word-qa/report.json`

**Interfaces:** consumes only `review.json` and `claims-timeline.png` in the audit directory.

- [ ] **Step 1: Implement the document**

Use CJK font channels, A4 margins, visible cached TOC plus real TOC field, Chinese header, PAGE-only footer, stable DXA tables, native Math API, and `features.updateFields=true`. Include source/direction, evidence comparison, numerical anchor, correction-priority, and open-boundary tables. Insert the timeline PNG after the evidence table with natural aspect ratio and caption. Add five native footnotes for PNAS, Song, Semenok, Crossref/Nature, and critical-manifold local evidence.

Use `MathFraction`/`MathSubScript` for the simplified temperature formula. Do not render math as an image. `.gitattributes` marks `sources/*.pdf binary`; `.gitignore` excludes `node_modules/`, `__pycache__/`, QA PNGs, and temporary files.

- [ ] **Step 2: Build and run contracts**

```bash
PATH="/c/Program Files/nodejs:$PATH" python "{kimi-word}/scripts/docx.py" check-docx /absolute/path/main-claims
PATH="/c/Program Files/nodejs:$PATH" python "{kimi-word}/scripts/docx.py" build /absolute/path/main-claims/build_report.js /absolute/path/main-claims/REVIEW.docx
python research/paper-direction-audit-2026-11-10/main-claims/test_main_claims_audit.py -v
python research/paper-direction-audit-2026-11-10/main-claims/verify_primary_sources.py -v
```

Expected: OOXML validation and all tests pass. Do not filter build output.

- [ ] **Step 3: Render and inspect once**

Run `docx.py render` once. If successful, read contact sheet first, then all pages and every content-loss/near-blank finding; record page observations and final DOCX SHA-256. On exit 4/5/6, record unavailable visual QA without retry.

---

### Task 4: Final verification and named-branch delivery

- [ ] **Step 1: Fresh final regression**

Run both test suites, JSON parsing for `review.json` and QA report, `docx.py validate`, and `git diff --check`. Require exit 0 for each and append command/output evidence to `run.log`.

- [ ] **Step 2: Commit and push**

```bash
git add research/paper-direction-audit-2026-11-10/main-claims docs/superpowers/plans/2026-11-10-main-claims-audit.md
git commit -m "docs: audit manuscript claims and experimental controversy"
git push -u origin audit/room-temp-claims-batch
git rev-parse HEAD
git ls-remote origin refs/heads/audit/room-temp-claims-batch
```

Require matching local/remote hashes and a clean worktree. Do not merge. Close only this six-document batch; leave the remaining room_temp_sc and full-repository audit open.

## Plan Self-Review

- Both positive and negative experimental sources are preserved with distinct evidence levels.
- The confirmed Nature citation mismatch is separated from unverified narrative details.
- The necessity claim is tested by real numerical counterexamples without excluding full theory.
- Previous-audit time boundaries are supplemented rather than hidden.
- All report formats share one JSON object; native figure, equations, tables, TOC, footnotes, and final-view QA are independently checked.
