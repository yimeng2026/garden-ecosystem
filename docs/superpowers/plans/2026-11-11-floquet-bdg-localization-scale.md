# Floquet-BdG Localization and Recovery-Scale Analysis Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session uses inline execution only; no subagent is permitted.

**Goal:** Determine whether the two N=320 non-recovered cases have defensible recovery-scale estimates, using basis-invariant subspace profiles and direct endpoint coverage rather than a single exponential fit.

**Architecture:** Reuse the original normalized rank-two subspace profiles for N=80/160/320. Compute direct two-end coverage, fixed-width endpoint masses, center mass, subspace IPR, and the existing separation ratio. Treat envelope fits as secondary diagnostics with explicit R², and emit a recovery estimate only when preregistered plateau criteria hold.

**Tech Stack:** Python 3, NumPy, SciPy `least_squares`, unittest, JSON/CSV, Matplotlib, docx-js for the final report.

## Global Constraints

- Use `research/floquet-bdg-disorder/profiles.npz` and its original `results.json`; these are normalized rank-two subspace profiles, not single-eigenvector IPR.
- Cases are exactly `(0.05,seed0)`, `(0.1,seed0)`, `(0.05,seed2)`, `(0.05,seed3)`, `(0.1,seed2)` at N=80/160/320, zero gap.
- Direct end coverage is `C_m=sum(profile[:m])+sum(profile[-m:])`; `L_p=min{m:C_m>=p}`. Never divide this cumulative sequence by two.
- Fixed absolute widths are `k=5,10,20,40`; center region is the middle 20% of sites. Also report `IPR=sum(profile²)` and `N*IPR`.
- Plateau criteria are: last-two `L50` relative change `<=0.25`, fixed-width-20 endpoint-mass ratio `>=0.8`, and N=320 separation ratio `<0.1`.
- Envelope fits report `xi_env`, background, amplitude, optimizer status, and R²; fits with R²<0.5 cannot justify an exponential recovery law.
- Next diagnostic size is `max(400,100*ceil(L50_latest/10))` only for non-recovered cases. It is a heuristic test size, never a predicted recovery size.
- No N=640 computation or claim is implied. Every estimate is marked `measured_recovered`, `bounded_diagnostic`, or `not_established`.

## File Map

- Create `research/floquet-bdg-localization-scale/scale_analysis.py`: coverage, masses, plateau assessment, and registry.
- Create `research/floquet-bdg-localization-scale/test_scale_analysis.py`: synthetic and real-data contracts.
- Create `research/floquet-bdg-localization-scale/analyze_scale.py`: original-profile extraction and JSON/CSV output.
- Create `research/floquet-bdg-localization-scale/localization_scale.json` and `.csv`: generated metrics and assessments.
- Create `research/floquet-bdg-localization-scale/build_report.py`: figures and Markdown.
- Create `research/floquet-bdg-localization-scale/build_report.js`: native Word.
- Create `research/floquet-bdg-localization-scale/run_verification.py`: one-command data, report, and visual-hash verification.

### Task 1: Coverage and Recovery Contracts

**Files:** Create `scale_analysis.py`, `test_scale_analysis.py`.

**Interfaces:** `coverage_lengths(profile, thresholds=(0.5,0.9,0.99))->dict`; `fixed_width_masses(profile,widths=(5,10,20,40))->dict`; `assess_recovery(rows)->dict`.

- [ ] **Step 1: Write synthetic coverage tests**

Use a normalized profile with nonzero values only at the first and last two sites. Require `C_2` to equal 1, not 0.5. Use a second nonuniform profile to verify that `L50`, `L90`, and `L99` are computed from direct two-end sums. Test center mass and `N*IPR` independently.

- [ ] **Step 2: Write plateau and growth tests**

A synthetic last-two `L50` sequence `(32,31)` with fixed-width-20 mass ratio `>=0.8` and separation `<0.1` must yield `bounded_diagnostic`. A sequence `(31,51)` must yield `not_established`, even if the profile has an apparent exponential fit. Already recovered N=320 cases yield `measured_recovered` and no required next size.

- [ ] **Step 3: Implement and run the tests**

Implement the metrics and assessment without consulting envelope fit outputs. Run all tests to pass, then commit with `feat: add direct endpoint coverage estimators`.

### Task 2: Original-Profile Analysis and Envelope Diagnostics

**Files:** Create `analyze_scale.py`, `localization_scale.json`, `localization_scale.csv`.

- [ ] **Step 1: Validate profile normalization and case registry**

Require all 15 profiles to have nonnegative entries, correct length, and sum within `1e-10` of 1. Cross-check N=320 edge weight and separation ratio against the original results. Any mismatch stops the analysis.

- [ ] **Step 2: Compute coverage, masses, IPR, and envelope diagnostics**

For every case and size, save `L50/L90/L99`, `L50/N`, fixed-width masses, center mass, `IPR`, `N*IPR`, edge weight, separation, `xi_env`, background, amplitude, optimizer success, and R². Do not hide a poor fit or an increasing L50.

- [ ] **Step 3: Apply recovery criteria and emit next diagnostic sizes**

Use only the preregistered plateau criteria. `bounded_diagnostic` stores the last-two L50 bracket multiplied by 10; `not_established` stores no recovery bracket. Non-recovered next size uses `max(400,100*ceil(L50_latest/10))` and is labeled heuristic.

### Task 3: Figures and Native Word Report

**Files:** Create `build_report.py`, `build_report.js`, figures, `REPORT.md`, and a Chinese-named DOCX.

- [ ] **Step 1: Generate direct coverage and endpoint-mass figures**

Plot L50/L90 by N for all five cases, fixed-width-20 mass, edge weight with the 0.5 threshold, `N*IPR`, and envelope R². Use sparse-point markers and do not draw a continuous phase boundary.

- [ ] **Step 2: Build and inspect the native Word**

Use docx-js with native formulas, true TOC, Chinese header, PAGE-only footer, stable tables, and numbered figures. Explain the earlier cumulative-definition correction, why L50=N/2 was not a localization length, and why the two next diagnostic sizes are N=400 and N=600 rather than a guaranteed N=640 recovery. Read the contact sheet and every final page.

- [ ] **Step 3: Verify and push**

Require data consistency, all 15 profiles, correct plateau outcomes, DOCX gate, visual hashes, and one-command verification to exit code 0. Commit and push only the named research branch.

## Plan Self-Review

- Direct two-end coverage fixes the earlier misleading cumulative-average metric.
- Fixed-width mass, IPR, separation, and R² prevent a single-fit or single-threshold interpretation.
- N=400 and N=600 are diagnostic tests selected by explicit formulas, not recovery predictions.
- Poor fits, growing tails, and already measured recoveries are reported without forcing a unified scale law.
