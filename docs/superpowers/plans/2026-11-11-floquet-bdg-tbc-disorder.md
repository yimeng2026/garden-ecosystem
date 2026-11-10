# Floquet-BdG TBC Disorder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session uses inline execution only; no subagent is permitted.

**Goal:** Compute preregistered per-realization TBC dynamical winding for N=80 disorder and matched uniform-mean controls, with independent determinant-phase checks and a fully reproducible report.

**Architecture:** Keep the validated static/clean runner unchanged. Add a disorder-only runner that refuses promotion unless the stored baseline passed, evaluates one strength per checkpoint to bound runtime, and merges only complete preregistered checkpoints. Reuse the fixed random sequence and open-chain endpoint helpers, while independently computing TBC winding for every sample and control.

**Tech Stack:** Python 3, NumPy, SciPy, unittest, JSON/CSV, Matplotlib, docx-js for the final native Word report; caches and temporary files under `D:/kimi-cache/tbc/`.

## Global Constraints

- Branch: `research/floquet-bdg-topology`; worktree: `.worktrees/room-temp-isotope-dft-audit`; no merge or prior-evidence edits.
- Admission requires `results.json.status == "clean_floquet_baseline_passed"` and `static.passed == true`.
- `N=80`, seeds `0,1,2,3`, strengths `0.05,0.1,0.2`; `beta=default_rng(20261111+seed).random(320)[:N]`.
- Disordered K-matrix parameter is `r*beta`; each separate uniform-mean control uses `r*np.ones(N)`. The half-kick rotation angle is `r*beta`, and the full symmetric rotation angle is `2*r*beta`; these two roles are not conflated. Superseded double-parameter checkpoints are retained under `diagnostics/double-kick/`.
- Winding uses nominal theta steps `0.05,0.025`, `gap_tolerance=1e-8`, condition limit `1e12`, integer and mesh tolerance `1e-3`.
- Every raw failure, nonconvergence, and undefined result is retained. No seed changes, post-hoc threshold tuning, eigenvalue averaging, or integer fabrication.
- Endpoint candidates remain observables, not a substitute for winding. A result is not called topologically robust from a majority vote alone.

## File Map

- Create `research/floquet-bdg-tbc/run_disorder.py`: admission, per-realization winding and endpoint evaluation, checkpoints, merge.
- Create `research/floquet-bdg-tbc/test_disorder.py`: fixed-sequence, amplitude, admission, control-separation, and checkpoint contracts.
- Create `research/floquet-bdg-tbc/disorder_r0p05.json`, `disorder_r0p10.json`, `disorder_r0p20.json`: generated strength checkpoints.
- Create `research/floquet-bdg-tbc/disorder_results.json` and `disorder_results.csv`: merged raw results and concise table.
- Create `research/floquet-bdg-tbc/verify_disorder.py`: independent determinant-phase checks on selected realizations and controls.
- Create `research/floquet-bdg-tbc/disorder_independent.json`: generated independent evidence.
- Create `research/floquet-bdg-tbc/build_disorder_report.py`: figure, Markdown, and report-table generation from observed JSON only.
- Create `research/floquet-bdg-tbc/build_word.py`: native Word generation after numerical evidence exists.
- Modify `research/floquet-bdg-tbc/run_verification.py`: add disorder tests and evidence hashes without weakening baseline checks.

### Task 1: Admission and Realization Contracts

**Files:** Create `run_disorder.py`, `test_disorder.py`.

**Interfaces:** `require_baseline(path: Path)->dict`; `beta_for(seed: int, n=80)->ndarray`; `evaluate_realization(n, seed, strength, kind, nominal_steps)->dict`; `run_strength(strength, n=80, seeds=(0,1,2,3), nominal_steps=(0.05,0.025))->dict`.

- [ ] **Step 1: Write failing admission and sample tests**

```python
class DisorderContractTests(unittest.TestCase):
    def test_fixed_sequence_and_full_kick_amplitude(self):
        beta = beta_for(0, 80)
        expected = np.random.default_rng(20261111).random(320)[:80]
        np.testing.assert_array_equal(beta, expected)
        row = evaluate_realization(8, 0, 0.05, "disorder", (0.2, 0.1))
        self.assertEqual(row["full_kick_parameter"], "K parameter r*beta; full symmetric rotation angle 2*r*beta")
        self.assertLess(row["half_kick_convention_error"], 1e-12)
        self.assertEqual(row["kind"], "disorder")
        self.assertEqual(row["seed"], 0)

    def test_uniform_control_is_separate(self):
        row = evaluate_realization(8, 0, 0.05, "uniform_mean", (0.2, 0.1))
        self.assertEqual(row["kind"], "uniform_mean")
        self.assertEqual(row["beta_sha256"], hashlib.sha256(np.ones(8).tobytes()).hexdigest())

    def test_baseline_failure_blocks_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"results.json"
            path.write_text(json.dumps({"status":"clean_floquet_baseline_failed"}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                require_baseline(path)
```

Run `python research/floquet-bdg-tbc/test_disorder.py -v`; expected failure is `ModuleNotFoundError: run_disorder`.

- [ ] **Step 2: Implement admission and one-realization evaluation**

`require_baseline` loads the stored file and raises unless both baseline flags pass. `beta_for` delegates to the existing verified `beta_sequence`. `evaluate_realization` rejects unknown `kind`, creates either the fixed disordered beta or a new ones vector, and calls:

```python
case = {"n": n, "mu0": np.full(n, 2.5), "mu1": strength*beta,
        "omega": 7.0, "gamma": 1.0, "delta": 1.0}
zero = winding_convergence(case, 0.0, nominal_steps, keep_curve=False)
pi = winding_convergence(case, np.pi, nominal_steps, keep_curve=False)
u, period = disordered_floquet(n, 2.5, beta, strength, 7.0, 1.0, 1.0)
spectrum = quasienergy_spectrum(u, period)
endpoint = {"zero": observe_candidate(spectrum, n, 1.0),
            "pi": observe_candidate(spectrum, n, -1.0)}
```

Remove each endpoint `profile` before JSON serialization; retain distances, separation ratios, edge weights, IPR, joint-pass fields, and open-chain unitarity. Store `beta_sha256`, `full_kick_parameter`, and all winding diagnostics.

- [ ] **Step 3: Run tests and commit the contract**

Expect all admission/sample tests to pass. Run `git diff --check` and commit with `test: add TBC disorder admission contracts`.

### Task 2: Strength Checkpoints and Complete Merge

**Files:** Modify `run_disorder.py`, `test_disorder.py`; generate three strength checkpoints and merged JSON/CSV.

**Interfaces:** `run_strength(...)->dict`; `merge_checkpoints(paths: list[Path])->dict`; CLI `--strength {0.05,0.1,0.2}` and `--merge-only`.

- [ ] **Step 1: Write failing checkpoint tests**

Require `run_strength(0.05,n=8,seeds=(0,1),nominal_steps=(0.2,0.1))` to return exactly four rows: two disordered and two uniform-mean, with each `(seed,kind)` unique. The full N=80 checkpoint has four seeds and therefore eight rows. Require a partial checkpoint list to raise `ValueError("incomplete preregistered disorder checkpoints")` rather than emitting a complete ensemble.

- [ ] **Step 2: Implement deterministic checkpointing**

For each seed, append the disordered row and its separate uniform-mean row. Write one file per completed strength with schema, parameters, baseline SHA-256, rows, and counts. Do not write a merged completion flag until all three files contain exactly eight N=80 rows, seeds `0..3`, both kinds, and the matching strength.

`merge_checkpoints` computes per-strength/kind/target counts of `status=="ok"`, nearest-integer frequencies, median raw value where defined, undefined count, and endpoint joint-pass count. These are descriptive ensemble summaries, not a topological theorem. Emit one CSV row per realization/target with raw winding, integer, gap, condition, mesh residual, endpoint separation, and edge weight.

- [ ] **Step 3: Execute bounded strength batches**

Run, separately, to stay within command time limits:

```bash
python research/floquet-bdg-tbc/run_disorder.py --strength 0.05
python research/floquet-bdg-tbc/run_disorder.py --strength 0.1
python research/floquet-bdg-tbc/run_disorder.py --strength 0.2
python research/floquet-bdg-tbc/run_disorder.py --merge-only
```

Each command must print its real row counts and exit code. A nonzero exit or incomplete JSON prevents a complete claim. Commit the runner and all observed checkpoints with `feat: compute preregistered TBC disorder winding`.

### Task 3: Independent Disorder Verification

**Files:** Create `verify_disorder.py`, `disorder_independent.json`; modify `test_disorder.py`.

**Interfaces:** `main()->int`, reading merged rows and calling `verify_tbc.determinant_winding` only for scalar uniform controls; for disordered rows use an independently written vector-mu reconstruction.

- [ ] **Step 1: Add independent vector-mu reconstruction**

Generalize the independent helper without calling production `winding` or `periodized`: accept vector `mu0` and `mu1`, build the symmetric time-ordered propagator and Schur branch explicitly, and unwrap `det(block)` on nominal step `0.0125` for N=80. Check half-period chiral error, requested gap, block condition, and integer residual.

- [ ] **Step 2: Verify fixed representative rows and every rejection category**

At minimum independently check seed `0` at each strength for both disorder and uniform mean, and both gaps. If any other realization is undefined or nonconverged, select one from each observed category and verify the rejection rather than hiding it. Compare independent integers only when both methods are valid; preserve disagreements as `agrees=false` and return exit code 1.

- [ ] **Step 3: Run and commit independent evidence**

Run `python research/floquet-bdg-tbc/verify_disorder.py`. Store exact commands, selected row identifiers, raw independent values, symmetry errors, and agreement flags. Commit with `test: independently verify TBC disorder winding`.

### Task 4: Figure, Native Word, and One-Command Regression

**Files:** Create report builders and generated artifacts; modify `run_verification.py`.

- [ ] **Step 1: Generate the numerical figure and Markdown**

Plot only observed data: per-realization winding for both gaps and both kinds, matched uniform controls, and min_bulk_gap on a logarithmic scale. Undefined points receive a distinct marker and are never rounded. The report states baseline corrections, raw disorder outcomes, ensemble limitations, and the unchanged prior `not_supported`/`inconclusive` scopes where applicable.

- [ ] **Step 2: Build and visually inspect native Word**

Use docx-js with real OMML equations, Chinese fonts, a true TOC field, Chinese header, PAGE-only footer, `cantSplit` table rows, numbered figures, and accurate source notes. Inspect the contact sheet and each final page image; exit codes 4/5/6 are not retried and LibreOffice is not used.

- [ ] **Step 3: Extend one-command verification and push**

Add disorder tests, checkpoint integrity, independent agreement, report consistency, and artifact hashes to `run_verification.py`. Run it to exit code 0, run `git diff --check`, commit all sources and evidence, and push only `research/floquet-bdg-topology`.

## Plan Self-Review

- The fixed sample, full-kick amplitude, separate mean controls, baseline gate, all three strengths, and per-realization raw outcomes are explicit.
- Checkpoints bound runtime without dropping failed realizations or allowing partial-ensemble completion.
- Independent checks reconstruct vector-disorder propagation rather than reusing the production winding result.
- Report generation cannot turn undefined results or majority votes into topological proof.
