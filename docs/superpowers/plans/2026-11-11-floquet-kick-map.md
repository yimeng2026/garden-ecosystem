# Uniform Kick Parameter Map and Disorder Decomposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Fock-checked homogeneous-kick amplitude/size map and decompose the existing disorder ensemble into mean-drive and fluctuation contributions without changing any prior verdict.

**Architecture:** Reuse the validated quadratic Kitaev and basis-invariant subspace modules. Compute homogeneous chains on a fixed grid with explicit gapless endpoint handling, then compare each stored disorder realization with its exact mean-matched uniform control. Deliver raw data, independent verification, figures and native Word.

**Tech Stack:** Python 3.12, NumPy 2.4.4, SciPy 1.18.1, `unittest`, Matplotlib, docx-js.

## Global Constraints

- Work only in the existing linked worktree on `research/floquet-kick-map`; no subagents, nested worktrees or main-branch merge.
- Fixed physical parameters: `γ=Δ=1`, `μ0=2.5`, `ω=7`, `ℏ=1`. Only the kick amplitude varies.
- Use the Fock-corrected `K[a,b]=−μ/2`, `(Δ−γ)/4`, `−(Δ+γ)/4`; never import the superseded matrix from `research/floquet-bdg/floquet_bdg.py`.
- Preserve `separation<0.1`, `edge_weight>0.5`, `inconclusive_preserved` and the previous disorder `not_supported` verdict.
- Endpoint singularities `a=0` and `a=π/14` must be labeled `gapless_or_undefined`, never assigned integer mode counts.
- Existing disorder and mean-control evidence is read-only. No new random seed, deleted failure or eigenvalue averaging as a single physical sample.
- Every verification script has `run_all_tests()`, a zero-test guard and real exit-code logging. Build caches go to D:.

---

### Task 1: Gapless-safe endpoint logic and uniform model

**Files:**
- Create: `research/floquet-kick-map/kick_map.py`
- Create: `research/floquet-kick-map/test_kick_map.py`
- Create: `research/floquet-kick-map/test-red.log`

**Interfaces:**
- Consumes: `disordered_floquet`, `observe_candidate`, `quasienergy_spectrum` from the two validated research packages.
- Produces: `uniform_floquet(n, a, omega=7.0, gamma=1.0, delta=1.0, mu0=2.5)`, `safe_endpoint_counts(a, mu0=2.5, gamma=1.0, omega=7.0)`, `evaluate_uniform(n, a)`.

- [ ] **Step 1: Write failing analytic and model contracts**

```python
def test_two_gapless_amplitudes_are_rejected():
    for a in (0.0, np.pi / 14):
        row = safe_endpoint_counts(a)
        assert row["status"] == "gapless_or_undefined"
        assert row["p0"] is None and row["p_pi"] is None

def test_uniform_model_matches_validated_clean_model():
    actual, _ = uniform_floquet(8, 0.1)
    expected, _ = kicked_floquet(8, 2.5, 0.1, 7.0)
    np.testing.assert_allclose(actual, expected, atol=1e-14)
```

Also assert `safe_endpoint_counts(0.1)["p0"] == 1`, `p_pi == 1`, `safe_endpoint_counts(0.25)["p_pi"] == 0`, and that the returned negative-hopping map is `k=0 → b_pi`, `k=π → b0`.

- [ ] **Step 2: Run RED and retain the real failure**

Run: `python research/floquet-kick-map/test_kick_map.py -v`
Expected: exit code 1 with `ModuleNotFoundError: No module named 'kick_map'`; save the command, key traceback and exit code to `test-red.log`.

- [ ] **Step 3: Implement the minimal uniform model and singularity gate**

```python
def uniform_floquet(n, a, omega=7.0, gamma=1.0, delta=1.0, mu0=2.5):
    if a < 0 or a >= np.pi / 2 or omega <= 0:
        raise ValueError("require 0 <= a < pi/2 and omega > 0")
    return disordered_floquet(n, mu0, np.ones(n), a, omega, gamma, delta)

def safe_endpoint_counts(a, mu0=2.5, gamma=1.0, omega=7.0):
    b0 = 4 * (mu0 - gamma) / omega + 2 * a / np.pi
    b_pi = 4 * (mu0 + gamma) / omega + 2 * a / np.pi
    singular = min(abs(b0 - round(b0)), abs(b_pi - round(b_pi))) < 1e-9
    if singular:
        return {"status": "gapless_or_undefined", "b0": b0, "b_pi": b_pi, "p0": None, "p_pi": None}
    low, high = sorted((b0, b_pi))
    integers = range(int(np.floor(low)) + 1, int(np.ceil(high)))
    return {"status": "ok", "b0": b0, "b_pi": b_pi,
            "p0": sum(n % 2 == 0 for n in integers),
            "p_pi": sum(n % 2 == 1 for n in integers)}
```

Check `U(0)` and `U(π)` against `diag(exp(±iπb_pi))` and `diag(exp(±iπb0))` respectively. Add `evaluate_uniform` returning the two `observe_candidate` records and unitarity error.

- [ ] **Step 4: Run analytic contracts and commit**

Run: `python research/floquet-kick-map/test_kick_map.py -v`
Expected: analytic tests PASS; artifact test still reports missing `results.json`.

```bash
git add research/floquet-kick-map/kick_map.py research/floquet-kick-map/test_kick_map.py research/floquet-kick-map/test-red.log
git commit -m "test: add gapless-safe uniform kick model"
```

---

### Task 2: Forty-five-point homogeneous map and contiguous islands

**Files:**
- Create: `research/floquet-kick-map/run_kick_map.py`
- Create: `research/floquet-kick-map/results.json`
- Create: `research/floquet-kick-map/uniform_grid.csv`
- Create: `research/floquet-kick-map/profiles.npz`

**Interfaces:**
- Consumes: Task 1 functions.
- Produces: 45 grid records and `pass_islands` grouped by `N` and target.

- [ ] **Step 1: Add artifact contracts before running the grid**

```python
def test_grid_has_45_records_and_two_singularities():
    data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
    assert len(data["grid"]) == 45
    assert sum(row["endpoint"]["status"] == "gapless_or_undefined" for row in data["grid"]) == 2
    assert data["sizes"] == [80, 160, 320, 640]
```

Require 14 amplitudes for each of `N=80,160,320`, plus only `a=0.05,0.1,0.2` for `N=640`. Check that all grid records contain both target observations and normalized profiles in NPZ.

- [ ] **Step 2: Implement the fixed grid without dropping singular points**

```python
AMPLITUDES = [0.0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15,
              0.175, 0.2, 0.22, np.pi / 14, 0.24, 0.25, 0.3]
LONG_CHAIN_AMPLITUDES = [0.05, 0.1, 0.2]
for n in (80, 160, 320):
    for a in AMPLITUDES:
        evaluate_and_append(n, a)
for a in LONG_CHAIN_AMPLITUDES:
    evaluate_and_append(640, a)
```

`evaluate_and_append` must call `evaluate_uniform` and `safe_endpoint_counts`, store profiles by `n{n}_a{a}_{target}`, and preserve each observation even when the analytic endpoint is singular.

- [ ] **Step 3: Record contiguous finite-size pass islands**

For each `N<640` and target, sort by amplitude and emit each contiguous run with `start`, `end`, `rows`, `endpoint_p0`, `endpoint_p_pi`, and `interval_semantics="grid_samples_not_a_precision_boundary"`. For `N=640`, emit `selected_amplitudes_only=true`, not an inferred interval. Record exact analytic singularities separately from grid-derived runs.

- [ ] **Step 4: Run the 45-point study and commit**

Run: `python research/floquet-kick-map/run_kick_map.py`
Expected: 45 records, two singular records, normalized profiles, both target observations per point. Run `test_kick_map.py -v` and require all grid contracts to pass.

```bash
git add research/floquet-kick-map/run_kick_map.py research/floquet-kick-map/results.json research/floquet-kick-map/uniform_grid.csv research/floquet-kick-map/profiles.npz research/floquet-kick-map/test_kick_map.py
git commit -m "feat: compute uniform kick parameter map"
```

---

### Task 3: Exact mean/fluctuation decomposition of the stored ensemble

**Files:**
- Create: `research/floquet-kick-map/decompose_disorder.py`
- Create: `research/floquet-kick-map/sensitivity.json`
- Create: `research/floquet-kick-map/sensitivity.csv`

**Interfaces:**
- Consumes: read-only `research/floquet-bdg-disorder/results.json`, `disorder_sequences.npz`, `realizations` and `mean_matched`.
- Produces: 216 per-target decomposition rows and grouped summaries.

- [ ] **Step 1: Write identity and category contracts**

```python
def test_amplitude_decomposition_is_exact():
    beta = beta_sequence(0, 160)
    r = 0.1
    a0 = r * beta.mean()
    np.testing.assert_allclose(r * beta, a0 + r * (beta - beta.mean()))
    row = decompose_realization(160, 0, r, "zero")
    assert row["mean_amplitude"] == a0
    assert row["category"] in {"both_pass", "fluctuation_sensitive", "uniform_fails", "fluctuation_assisted"}
```

Define categories mechanically: `both_pass` (uniform and disorder pass), `fluctuation_sensitive` (uniform passes, disorder fails), `uniform_fails` (uniform fails, disorder fails), `fluctuation_assisted` (uniform fails, disorder passes). These are outcome labels, not claims of topological creation or destruction.

- [ ] **Step 2: Compute per-realization fluctuation metrics**

```python
fluctuation = r * (beta - beta.mean())
row = {
    "mean_amplitude": r * beta.mean(),
    "fluctuation_rms": float(np.sqrt(np.mean(fluctuation**2))),
    "distance_delta": max(disorder["distances"]) - max(uniform["distances"]),
    "edge_delta": disorder["edge_weight"] - uniform["edge_weight"],
    "subspace_ipr_delta": disorder["subspace_ipr"] - uniform["subspace_ipr"],
}
```

Store all 216 rows and group by `N`, `r`, target and category. Report median absolute deltas and outcome-change counts without rounding the underlying records.

- [ ] **Step 3: Verify the decomposition and commit**

Run: `python research/floquet-kick-map/decompose_disorder.py`
Expected: 216 rows, exact amplitude identity, 108 original realizations and 108 uniform controls unchanged. Add a test that `N=160,r=0.1,zero` has `fluctuation_sensitive=15`, `both_pass=1`, while `pi` has `both_pass=16`.

```bash
git add research/floquet-kick-map/decompose_disorder.py research/floquet-kick-map/sensitivity.json research/floquet-kick-map/sensitivity.csv research/floquet-kick-map/test_kick_map.py
git commit -m "feat: decompose disorder sensitivity by mean drive"
```

---

### Task 4: Independent verification, figures, native Word and delivery

**Files:**
- Create: `research/floquet-kick-map/verify_kick_map.py`
- Create: `research/floquet-kick-map/build_figure.py`
- Create: `research/floquet-kick-map/build_markdown.py`
- Create: `research/floquet-kick-map/build_report.js`
- Create: `research/floquet-kick-map/test_report.py`
- Create: `research/floquet-kick-map/run_verification.py`
- Create: `research/floquet-kick-map/record_word_qa.py`

**Interfaces:**
- Consumes: all Task 1–3 artifacts.
- Produces: independently checked report, four-page visual review, verification log and pushed branch.

- [ ] **Step 1: Independently reconstruct the model and raw outcomes**

`verify_kick_map.py` must rebuild `U=K(a)FK(a)` for `N=160,a=0.1`, check unitarity and candidate metrics, confirm `U(k=0)` is `+I` within `1e-10` at `a=π/14`, recompute pass counts and test subspace rotation invariance. Assert the original disorder verdict remains `not_supported` and no disorder winding was computed.

- [ ] **Step 2: Generate four data-driven panels**

Panel A/B: homogeneous 0/π pass maps across all 14 amplitudes and `N=80,160,320`, with singular points explicitly marked. Panel C: `N=160,r=0.1` per-seed disorder and uniform edge weights. Panel D: mechanical category counts from Task 3. Do not select the best seed or hide `a=0` and `a=π/14`.

- [ ] **Step 3: Generate Markdown and native Word with current values**

Use a real TOC, Chinese header, PAGE-only footer, `cantSplit`, native OMML and footnotes for `arXiv:1303.2300`, `arXiv:2203.16353`, `results.json`, `sensitivity.json` and `verify_kick_map.py`. Distinguish analytic boundaries, finite grid samples and mechanical fluctuation categories. Preserve `not_supported` and `inconclusive_preserved`.

Run the docx-js build gate, then render once. Read the contact sheet and every page. Exit 4/5/6 means unavailable: no retry or LibreOffice, and no visual-pass claim.

- [ ] **Step 4: Run complete regression and verify artifact identity**

`run_verification.py` must execute the map, decomposition, analytic tests, independent tests, figure/Markdown builders and report contracts with real exit codes. Record JSON and DOCX SHA-256 values and compare them with `word-qa/report.json`.

```bash
python research/floquet-kick-map/run_verification.py
python research/floquet-kick-map/record_word_qa.py
git diff --check
```

Expected: all commands exit 0; raw 45-point grid and 216 decomposition rows agree with the report.

- [ ] **Step 5: Commit, push and retain the worktree**

```bash
git add research/floquet-kick-map docs/superpowers/plans/2026-11-11-floquet-kick-map.md
git commit -m "feat: map homogeneous kick robustness and disorder sensitivity"
git push -u origin research/floquet-kick-map
git rev-parse HEAD
git ls-remote origin refs/heads/research/floquet-kick-map
```

Require matching local and remote hashes and a clean status. Mark every completed checkbox only after its actual command succeeds. Do not merge main and do not claim material `Tc`, a thermodynamic-limit theorem, disorder topology or experimental validation.
