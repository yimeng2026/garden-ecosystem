# Floquet-BdG TBC N=320 Targeted Zero-Gap Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session uses inline execution only; no subagent is permitted.

**Goal:** Compute N=320 zero-gap TBC winding for endpoint-recovered and non-recovered controls using a measured Hermitian-eigensolver acceleration, without changing the validated Schur periodization or scientific criteria.

**Architecture:** Keep `expm` as the default for existing runs. Add an explicit `free_method="eigh"` option only for targeted N=320 cases, reconstructing the same free propagator from `eigh(iK)` and verifying unitarity. Reuse target-only realization evaluation and write one checkpoint per case.

**Tech Stack:** Python 3, NumPy, SciPy `eigh`/`expm`/`schur`, unittest, JSON, existing corrected TBC model; caches under `D:/kimi-cache/tbc/`.

## Global Constraints

- Named branch and existing isolated worktree only; no merge, subagent, seed change, threshold change, or endpoint-only inference.
- N=320, zero gap, nominal theta steps `0.05,0.025`, same chiral, gap, condition, integer, and mesh criteria as N=80/N=160.
- K-matrix parameter remains `r*beta`; `beta=default_rng(20261111+seed).random(320)` uses the full N=320 sequence.
- Seven cases: recovered `(0.05,seed2)`, `(0.05,seed3)`, `(0.1,seed2)`; non-recovered `(0.05,seed0)`, `(0.1,seed0)`; uniform controls `r=0.05,0.1`.
- `eigh(iK)` must reconstruct `expm` within `1e-10` on comparison cases. Schur periodization and independent determinant checks remain in place.
- One-grid convergence is not accepted as two-grid convergence. Missing cases and failed cases remain explicit.

## File Map

- Modify `research/floquet-bdg-tbc/tbc_model.py`: optional free-propagator backend; default remains `expm`.
- Modify `research/floquet-bdg-tbc/run_disorder.py`: pass optional backend through target-only evaluation.
- Create `research/floquet-bdg-tbc/run_n320.py`: seven-case registry and incremental N=320 checkpoints.
- Create `research/floquet-bdg-tbc/test_n320.py`: backend equivalence, registry, and single-grid rejection contracts.
- Create `research/floquet-bdg-tbc/n320_zero.json`: generated seven-case evidence.
- Create `research/floquet-bdg-tbc/verify_n320.py`: independent determinant-phase checks for failures and representatives.
- Create `research/floquet-bdg-tbc/N320.md`, figures, and native Word supplement after all seven cases complete.

### Task 1: Backend Equivalence and Convergence Guard

**Files:** Modify `tbc_model.py`, `run_disorder.py`; create `test_n320.py`.

**Interfaces:** `free_evolution(k0,time,method="expm")`; `winding(...,free_method="expm")`; `winding_convergence(...,free_method="expm")`; `evaluate_realization(...,free_method="expm")`.

- [ ] **Step 1: Write failing equivalence tests**

For N=40, `r=0.05`, seed2, and `theta=0.037`, assert `free_evolution(k0,period/2,"eigh")` differs from `free_evolution(...,"expm")` by less than `1e-10`, and `U†U=I` within `1e-10`. Compare one zero-gap winding at nominal steps `0.1,0.05` between backends and require raw-value difference below `1e-9`.

Add a contract that `winding_convergence(..., nominal_steps=(0.05,))` raises `ValueError` instead of claiming convergence from one grid.

- [ ] **Step 2: Implement the optional backend**

For `method="eigh"`, diagonalize the Hermitian matrix `iK` and reconstruct `Q exp(2 i E t) Q†`, since `K=-i(iK)`. Check Hermiticity and unitarity. Keep `method="expm"` as the unchanged default. Pass the option through `winding_convergence` and realization evaluation. Require exactly two nominal grids for production convergence claims.

- [ ] **Step 3: Run all baseline and finite-size tests**

Run `test_tbc.py`, `test_disorder.py`, `test_finite_size.py`, and `test_n320.py`. All must pass before any N=320 computation. Commit with `feat: add validated Hermitian free-evolution backend`.

### Task 2: Seven-Case N=320 Registry

**Files:** Create `run_n320.py`, `test_n320.py`, `n320_zero.json`.

**Interfaces:** `n320_registry()->list[dict]`; `run_n320(selector=None,path=ROOT/"n320_zero.json")->dict`; `merge_n320(path)->dict`.

- [ ] **Step 1: Write registry and checkpoint tests**

Assert the exact seven unique cases and no others. A partial file must raise `ValueError("incomplete N320 case registry")`. Each row records `free_method="eigh"`, runtime, beta hash, and half-kick error.

- [ ] **Step 2: Implement per-case atomic checkpoints**

Use `evaluate_realization(...,targets=("zero",),free_method="eigh")`. Preserve existing rows and skip completed cases. `complete` becomes true only for all seven N=320 rows with correct sequence hashes and half-kick errors `<=1e-12`.

- [ ] **Step 3: Execute one case per command**

Representative commands:

```bash
python research/floquet-bdg-tbc/run_n320.py --kind disorder --strength 0.05 --seed 2
python research/floquet-bdg-tbc/run_n320.py --kind disorder --strength 0.05 --seed 3
python research/floquet-bdg-tbc/run_n320.py --kind disorder --strength 0.1 --seed 2
python research/floquet-bdg-tbc/run_n320.py --kind disorder --strength 0.05 --seed 0
python research/floquet-bdg-tbc/run_n320.py --kind disorder --strength 0.1 --seed 0
python research/floquet-bdg-tbc/run_n320.py --kind uniform_mean --strength 0.05
python research/floquet-bdg-tbc/run_n320.py --kind uniform_mean --strength 0.1
```

If a case exceeds the command limit, preserve any partial evidence and implement per-theta resume rather than weakening grid or gap criteria. Commit observed rows without calling the registry complete early.

### Task 3: Independent N=320 Verification

**Files:** Create `verify_n320.py`, `n320_independent.json`.

- [ ] **Step 1: Verify every failure category and recovered case**

Use independent Schur/`expm` determinant-phase reconstruction for every nonconverged or undefined case and the three endpoint-recovered cases. Do not use the accelerated backend as its own only verification.

- [ ] **Step 2: Verify controls and compare endpoints**

Check both uniform controls and both non-recovered seed0 cases. Compare N=320 winding with N=320 endpoint joint pass, edge weight, and separation. Distinguish finite-size crossover from bulk-boundary failure; retain every disagreement.

- [ ] **Step 3: Store bounded independent batches**

Checkpoint each independent case separately and merge only all seven required checks. A failed or missing check prevents completion.

### Task 4: N=320 Report and Unified Regression

**Files:** Create figures, `N320.md`, native Word supplement; modify `run_verification.py`.

- [ ] **Step 1: Generate the N=320 comparison figure**

Plot winding, bulk gap, and existing endpoint observables for recovered and non-recovered cases separately. Do not connect sparse points as a phase boundary.

- [ ] **Step 2: Build and inspect the native Word supplement**

Use docx-js, native equations, true TOC, Chinese header, PAGE-only footer, stable tables, and numbered figures. Read the contact sheet and every page; no LibreOffice or retry for unavailable render.

- [ ] **Step 3: Extend regression and push**

Add backend equivalence, seven-case registry, independent agreement, report consistency, and artifact hashes. Run required commands to exit code 0, then commit and push the named branch. The broader research goal remains active.

## Plan Self-Review

- The speedup comes only from a measured Hermitian decomposition; Schur and physical criteria are unchanged.
- The registry includes recovered and non-recovered cases plus separate uniform controls, avoiding success-only sampling.
- No one-grid result, partial checkpoint, or endpoint observation is promoted to a two-grid or bulk-winding conclusion.
- Independent checks use the original Schur/`expm` path and preserve N=320 evidence boundaries.
