# Floquet-BdG N=400 Threshold Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session uses inline execution only; no subagent is permitted.

**Goal:** Compute N=400 zero-gap TBC winding for `r=0.1, seed=0` without exceeding command limits, while preserving nested randomness, both theta grids, and all original convergence criteria.

**Architecture:** Extend the existing RNG stream rather than creating a new one. Refactor one-theta chiral-block evaluation out of the established winding function, then add resumable chunks that persist scalar integrands and only the first/last two chiral blocks. Aggregate two completed grids with the unchanged convergence function and independently verify determinant phase.

**Tech Stack:** Python 3, NumPy, SciPy, unittest, JSON, D-drive block cache, existing `eigh` free propagation and Schur periodization.

## Global Constraints

- Named branch and existing isolated worktree only; no merge, subagent, new seed, grid reduction, or threshold change.
- `N=400`, `r=0.1`, `seed=0`, zero gap, nominal theta steps `0.05,0.025`, `free_method="eigh"`.
- `beta_N=default_rng(20261111+seed).random(N)` for N>320; its first 320 values must exactly match the existing sequence. N<=320 continues to call the original `beta_sequence`.
- Each grid checkpoint stores scalar integrands and diagnostics in the workspace. Only the first two and most recent two chiral blocks are stored, under `D:/kimi-cache/tbc/large-diagnostic/`; never store all theta blocks on C.
- `chunk_size=8` and `max_chunks=4` per command are the default resource bounds. A killed chunk is recomputed from its first unfinished index, with no scalar-integrand duplication.
- No result is aggregated until both grids are complete. Missing or failed points preserve `undefined`/`not_converged`; no integer fabrication.
- N=600 reuses the same machinery only after N=400 and the nested-stream tests pass.

## File Map

- Modify `research/floquet-bdg-tbc/tbc_model.py`: one-theta block helper and integrand-based winding aggregation; existing `winding` behavior remains the default reference.
- Modify `research/floquet-bdg-tbc/run_disorder.py`: nested RNG extension for N>320.
- Create `research/floquet-bdg-tbc/resumable_winding.py`: chunk state, D-drive block cache, resume and final aggregation.
- Create `research/floquet-bdg-tbc/run_scale_diagnostic.py`: N=400/N=600 case registry, per-grid resume, and case aggregation.
- Create `research/floquet-bdg-tbc/test_resumable.py`: nested RNG, chunk-resume, duplicate prevention, and reference-equivalence tests.
- Create `research/floquet-bdg-tbc/scale_diagnostic.json`: generated case evidence.
- Create `research/floquet-bdg-tbc/verify_scale_diagnostic.py`: independent determinant-phase checks.
- Create `research/floquet-bdg-tbc/SCALE_DIAGNOSTIC.md`, figures, and native Word after the N=400 case completes.

### Task 1: Nested RNG and One-Theta Reference Contract

**Files:** Modify `run_disorder.py`, `tbc_model.py`; create `test_resumable.py`.

**Interfaces:** `beta_for(seed,n)`; `half_chiral_block(parameters,theta,epsilon,free_method="expm")->dict`; `winding_from_integrands(rows,metadata)->dict`.

- [ ] **Step 1: Write failing nested-stream tests**

Require `beta_for(0,400)[:320]` to equal `beta_for(0,320)` exactly, length 400, and `beta_for(0,600)[:400]` to equal `beta_for(0,400)` exactly. N=80/160/320 behavior must remain unchanged.

- [ ] **Step 2: Write one-theta reference tests**

At N=20, `r=0.1`, seed0, and `theta=0.037`, require `half_chiral_block(...,free_method="eigh")` to return a valid chiral block, open bulk gap, finite condition, and unitarity error below `1e-9`.

- [ ] **Step 3: Implement the helper without changing existing results**

Extract the existing per-theta propagation, Schur periodization, and block extraction into `half_chiral_block`. Keep `winding` as the reference implementation and verify its results do not change.

### Task 2: Resumable Scalar-Integrand Chunks

**Files:** Create `resumable_winding.py`, `test_resumable.py`.

**Interfaces:** `resumable_winding(parameters,nominal_step,epsilon,work_path,free_method="eigh",chunk_size=8,max_chunks=4)->dict`.

- [ ] **Step 1: Write failing chunk-resume tests**

Use N=20, nominal step `0.2`, `chunk_size=2`, `max_chunks=1`. The first call processes exactly two theta points and returns `status="partial"` with no winding integer. The second call resumes from the next index. Repeated calls never duplicate an integrand.

- [ ] **Step 2: Require reference-equivalent final aggregation**

After all points complete, compare raw winding, status, gap, condition, and integer with the existing `winding` at the same parameters. Require raw-value difference below `1e-10` for both `expm` and `eigh`. Verify that only the first two and most recent two block matrices are present in the D-drive cache.

- [ ] **Step 3: Implement bounded scalar checkpoints**

At point j, use the current and two preceding blocks to compute the integrand for j-1. Save it only when the chunk completes. Store first blocks B0/B1 and the latest two blocks in D cache. On resume, continue from the first unfinished index. At the final point, add periodic wrap integrands for j=0 and j=m-1 and apply the same raw winding and quantization formulas as the reference.

- [ ] **Step 4: Run all baseline and resume tests**

Run `test_tbc.py`, `test_disorder.py`, `test_n320.py`, and `test_resumable.py`. All must pass before N=400. Commit with `feat: add resumable scalar-integrand winding`.

### Task 3: N=400 Case and Independent Verification

**Files:** Create `run_scale_diagnostic.py`, `verify_scale_diagnostic.py`, `scale_diagnostic.json`.

**Interfaces:** `diagnostic_registry()->list[dict]`; `run_diagnostic_case(case,grid,max_chunks=4)->dict`; `merge_diagnostics(path)->dict`.

- [ ] **Step 1: Register N=400 and N=600 without computing both blindly**

N=400 is `r=0.1, seed=0`; N=600 is `r=0.05, seed=0`. Each has `recovered=False` at N=320 and a distinct evidence rationale. `complete` requires both only when the owner explicitly advances to N=600; N=400 has its own completion flag.

- [ ] **Step 2: Execute per-grid bounded batches**

Representative commands:

```bash
python research/floquet-bdg-tbc/run_scale_diagnostic.py --n 400 --grid 0.05 --max-chunks 4
python research/floquet-bdg-tbc/run_scale_diagnostic.py --n 400 --grid 0.025 --max-chunks 4
```

Repeat the second command until its grid completes, then aggregate with `winding_convergence_from_rows`. Store open-chain endpoint observables from the same nested beta and compare with N=320.

- [ ] **Step 3: Independently verify determinant phase**

Use original `expm+Schur` determinant reconstruction for N=400, zero gap, and compare the independent integer with both grids. Independently check any nonconvergence instead of hiding it.

### Task 4: Diagnostic Report and Next-Size Decision

**Files:** Create `SCALE_DIAGNOSTIC.md`, figures, native Word; modify `run_verification.py`.

- [ ] **Step 1: Generate the N=400 comparison figure**

Plot W0, bulk gap, endpoint weight, separation, and N=320/N=400 coverage metrics. Preserve the prior `bounded_diagnostic` rationale without turning N=400 into a recovery promise.

- [ ] **Step 2: Build and inspect the native Word supplement**

Use native equations, true TOC, Chinese header, PAGE-only footer, stable tables, and numbered figures. Read the contact sheet and every page; no LibreOffice or retry for unavailable render.

- [ ] **Step 3: Decide whether N=600 is justified**

If N=400 clarifies the threshold crossing, report whether N=600 would test a distinct remaining mechanism. If N=400 remains near the same threshold or is numerically undefined, do not claim closure; keep N=600 as an independent tail-growth diagnostic rather than an automatic success prediction.

- [ ] **Step 4: Verify and push**

Require nested-stream hashes, all grid checkpoints, independent agreement, report consistency, and visual hashes. Run required commands to exit code 0 and push only the named branch.

## Plan Self-Review

- RNG extension is nested and exact, not a new random ensemble.
- Chunking stores scalar integrands and at most four boundary blocks, avoiding C-disk growth from full matrix histories.
- Final aggregation uses the same two-grid formula and is tested against the existing winding implementation.
- N=400 is a threshold diagnostic; N=600 remains a separate mechanism test, not an automatic recovery prediction.
