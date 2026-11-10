# Floquet-BdG TBC Finite-Size Zero-Gap Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session uses inline execution only; no subagent is permitted.

**Goal:** Test whether N=160 zero-gap bulk winding remains quantized while the corresponding open-chain endpoint candidates still fail, using targeted disorder realizations and separate uniform controls.

**Architecture:** Reuse the corrected realization evaluator and add a target-only mode so each N=160 case computes only the zero gap. Checkpoint every case before starting another, merge only the preregistered 11-case set, and independently recompute determinant phase for every nonconverged case plus representative valid controls.

**Tech Stack:** Python 3, NumPy, SciPy, unittest, JSON/CSV, existing Fock-checked Majorana and TBC implementations; caches under `D:/kimi-cache/tbc/`.

## Global Constraints

- Branch `research/floquet-bdg-topology`, existing isolated worktree only; no merge, subagent, seed change, threshold change, or prior-evidence edits.
- `N=160`, `mu0=2.5`, `omega=7`, `gamma=delta=1`, zero gap only, nominal theta steps `0.05,0.025`.
- K-matrix onsite parameter is `r*beta`; half-kick angle is `r*beta`, full symmetric rotation angle is `2*r*beta`.
- Cases are exactly three uniform controls `(r=0.05,0.1,0.2)` and disorder `(r=0.05,0.1) × seeds(0,1,2,3)`, totaling 11.
- `beta=default_rng(20261111+seed).random(320)[:160]`; nested sequence must match the first 160 entries of the N=320 protocol.
- Every valid, undefined, and nonconverged result is retained. No integer is assigned after failure.
- Existing N=160/N=320 open-chain endpoint observations are evidence for comparison, not a substitute for new TBC winding.

## File Map

- Modify `research/floquet-bdg-tbc/run_disorder.py`: optional target subset without changing default two-gap behavior.
- Create `research/floquet-bdg-tbc/run_finite_size.py`: case registry, incremental N=160 checkpoints, merge.
- Create `research/floquet-bdg-tbc/test_finite_size.py`: case registry, target-only, sequence, and incomplete-merge contracts.
- Create `research/floquet-bdg-tbc/finite_size_zero.json`: generated 11-case evidence.
- Create `research/floquet-bdg-tbc/verify_finite_size.py`: independent determinant-phase checks for failures and representatives.
- Create `research/floquet-bdg-tbc/finite_size_independent.json`: generated independent evidence.
- Create `research/floquet-bdg-tbc/FINITE_SIZE.md`, figure, and native Word supplement after all 11 cases and independent checks are complete.

### Task 1: Target-Only Evaluation Contract

**Files:** Modify `run_disorder.py`; create `test_finite_size.py`.

**Interfaces:** `evaluate_realization(n, seed, strength, kind, nominal_steps, targets=("zero","pi"))->dict`; default behavior remains unchanged.

- [ ] **Step 1: Write a failing target-only test**

```python
row = evaluate_realization(8, 0, 0.05, "disorder", (0.2, 0.1), targets=("zero",))
assert "zero" in row and "pi" not in row
assert row["half_kick_convention_error"] < 1e-12
```

Run `python research/floquet-bdg-tbc/test_finite_size.py -v`; expected failure is the unexpected `targets` argument.

- [ ] **Step 2: Implement target validation and conditional evaluation**

Require `targets` to be a nonempty tuple/list containing only `"zero"` or `"pi"`, with no duplicates. Compute `winding_convergence` and open-chain endpoint observation only for requested targets. Preserve `full_kick_parameter`, `half_kick_convention_error`, and all other row metadata.

- [ ] **Step 3: Run old and new tests**

Run `test_disorder.py -v` and `test_finite_size.py -v`; all must pass. Commit with `feat: allow target-only TBC realization evaluation`.

### Task 2: Preregistered N=160 Case Registry and Checkpoints

**Files:** Create `run_finite_size.py`, `test_finite_size.py`, `finite_size_zero.json`.

**Interfaces:** `case_registry()->list[dict]`; `run_cases(n=160, selector=None, path=ROOT/"finite_size_zero.json")->dict`; `merge_complete(path)->dict`.

- [ ] **Step 1: Write registry and incomplete-merge tests**

Assert exactly 11 unique `(strength,seed,kind,target)` cases. Uniform controls occur once per strength and use `kind="uniform_mean"`; all targets are `"zero"`. Check nested beta equality with `default_rng(20261111+seed).random(320)[:160]`. A file with fewer than 11 rows must raise `ValueError("incomplete finite-size case registry")`.

- [ ] **Step 2: Implement incremental case execution**

Each case calls `evaluate_realization(..., targets=("zero",))`, records runtime and checkpoint SHA-256, and writes atomically after every case. Existing rows are retained byte-for-byte; duplicate rows are not recomputed. `complete` becomes true only when all 11 unique rows are present and every `half_kick_convention_error <= 1e-12`.

- [ ] **Step 3: Execute bounded batches**

Use one seed or one uniform control per command for N=160. A representative command is:

```bash
python research/floquet-bdg-tbc/run_finite_size.py --kind disorder --strength 0.05 --seed 2
```

Run the remaining cases in any order, then `python research/floquet-bdg-tbc/run_finite_size.py --merge-only`. Preserve actual exit codes and never infer missing rows from N=80 or N=320.

### Task 3: Independent Finite-Size Verification

**Files:** Create `verify_finite_size.py`, `finite_size_independent.json`.

- [ ] **Step 1: Independently verify every failure category**

For each `not_converged`, `gapless_or_undefined`, or invalid-chiral row, reconstruct vector-mu propagation and unwrap `det(block)` without calling the production integrator. Use nominal theta step `0.05` for the regression check and retain finer-grid evidence when already available.

- [ ] **Step 2: Verify representative valid cases**

At minimum check one disordered valid row at each strength, the three uniform controls, and any row whose winding integer differs between N=80 and N=160. Preserve disagreements rather than forcing agreement.

- [ ] **Step 3: Compare with open-chain trends**

Tabulate N=80/N=160/N=320 endpoint edge weight, separation ratio, and joint pass for the same seeds and strengths. Separate finite-size crossover evidence from bulk-boundary failure; N=160 alone cannot establish a thermodynamic limit.

### Task 4: Supplementary Report and Regression

**Files:** Create figure, `FINITE_SIZE.md`, native Word supplement; modify `run_verification.py`.

- [ ] **Step 1: Generate the size-trend figure**

Plot only observed zero-gap winding and open-chain endpoint quantities by N and seed. Mark nonconvergence separately and do not connect sparse points as if they proved a continuous phase boundary.

- [ ] **Step 2: Build and inspect the native Word supplement**

Use docx-js, OMML, true TOC, Chinese header, PAGE-only footer, stable tables, numbered figures, and exact data notes. Read the contact sheet and every final page image; no LibreOffice and no retries for render exit 4/5/6.

- [ ] **Step 3: Verify and push**

Extend regression with registry integrity, independent agreement, report consistency, and SHA-256. Run all required commands to exit code 0, then commit and push only the named branch. Do not mark the broader research goal complete after this finite-size slice.

## Plan Self-Review

- The 11-case registry directly targets the unresolved zero-gap finite-size question without an unaffordable full N=320 sweep.
- Target-only evaluation reuses the corrected amplitude contract and does not alter default two-gap results.
- Failure categories, representative valid cases, and N=80/N=160/N=320 endpoint trends are independently distinguished.
- No missing case, repeated uniform control, or determinant-phase result is misrepresented as an independent random ensemble or a thermodynamic proof.
