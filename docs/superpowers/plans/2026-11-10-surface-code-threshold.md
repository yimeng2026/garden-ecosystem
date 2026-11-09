# Surface Code Threshold Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a real, independently verifiable Stim＋PyMatching surface-code threshold benchmark with 28 circuit-level Monte Carlo grid points.

**Architecture:** A frozen JSON protocol drives a small standard-library statistics layer and a Stim/PyMatching runner. A separate verifier recomputes rates, Wilson intervals, crossing estimates and hashes from immutable result files; documentation distinguishes this protocol from the paper's missing original simulation.

**Tech Stack:** Python 3.12 standard library, Stim, PyMatching, NumPy, unittest, JSON/CSV/SVG.

## Global Constraints

- No synthetic logical-error values: every reported `errors` must come from `actual_observables != predicted_observables` on real Stim samples.
- Do not fall back to the paper's scaling formula when Stim or PyMatching is unavailable.
- Distances are `[3,5,7,9]`, probabilities are `[0.004,0.005,0.006,0.007,0.008,0.009,0.010]`, and each point uses 20,000 shots.
- The crossing estimate is exploratory, not an FSS fit or a confidence interval.
- All generated artifacts stay under `research/paper-direction-audit-2026-11-10/surface-code-threshold/`; dependencies stay under ignored `.tools/`.
- No background service or subprocess is left running.

---

### Task 1: Protocol and statistical kernel

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/surface-code-threshold/protocol.json`
- Create: `research/paper-direction-audit-2026-11-10/scripts/surface_code_stats.py`
- Test: `research/paper-direction-audit-2026-11-10/tests/test_surface_code_stats.py`

**Interfaces:**
- Produces: `validate_protocol(dict)->dict`, `wilson_interval(errors:int,shots:int,z:float=1.959963984540054)->tuple[float,float,float]`, `crossing(xs:list[float],small:list[float],large:list[float])->float`, `estimate_crossings(points:list[dict])->dict`.

- [ ] **Step 1: Write failing tests**

```python
import unittest
from surface_code_stats import validate_protocol, wilson_interval, crossing, estimate_crossings

class StatisticsTests(unittest.TestCase):
    def test_wilson_handles_boundaries_and_center(self):
        self.assertEqual(wilson_interval(0, 100)[0], 0.0)
        self.assertEqual(wilson_interval(100, 100)[2], 1.0)
        rate, low, high = wilson_interval(50, 100)
        self.assertEqual(rate, 0.5)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_crossing_is_exact_on_synthetic_lines(self):
        xs = [0.006, 0.008]
        small = [-0.3, -1.3]
        large = [-1.3, -0.3]
        self.assertAlmostEqual(crossing(xs, small, large), 0.007)

    def test_crossing_rejects_non_crossing_lines(self):
        with self.assertRaises(ValueError):
            crossing([0.006, 0.008], [-0.3, -0.4], [-1.3, -1.4])

    def test_protocol_rejects_even_distance_and_bad_probability(self):
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [4], "probabilities": [0.005], "shots": 10})
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [3], "probabilities": [1.2], "shots": 10})

    def test_crossing_estimator_preserves_pair_and_range(self):
        points = []
        for distance, small, large in [(3, -0.3, -1.3), (5, -1.3, -0.3)]:
            for index, p in enumerate([0.006, 0.008]):
                points.append({"distance": distance, "p": p,
                               "log10_rate": (small if distance == 3 else large)[index]})
        result = estimate_crossings(points)
        self.assertEqual(result["crossings"][0]["pair"], [3, 5])
        self.assertAlmostEqual(result["median"], 0.007)
        self.assertAlmostEqual(result["minimum"], 0.007)
        self.assertAlmostEqual(result["maximum"], 0.007)
```

Run: `PYTHONPATH=research/paper-direction-audit-2026-11-10/scripts python -m unittest research/paper-direction-audit-2026-11-10/tests/test_surface_code_stats.py -v`  
Expected: FAIL because `surface_code_stats` does not exist.

- [ ] **Step 2: Implement the statistical kernel**

```python
def wilson_interval(errors, shots, z=1.959963984540054):
    if isinstance(errors, bool) or isinstance(shots, bool):
        raise ValueError("invalid counts")
    if not isinstance(errors, int) or not isinstance(shots, int) or shots <= 0 or not 0 <= errors <= shots:
        raise ValueError("invalid counts")
    rate = errors / shots
    denominator = 1 + z*z/shots
    center = (rate + z*z/(2*shots)) / denominator
    radius = z * ((rate*(1-rate)/shots + z*z/(4*shots*shots)) ** 0.5) / denominator
    return rate, max(0.0, center-radius), min(1.0, center+radius)


def crossing(xs, small, large):
    differences = [a-b for a, b in zip(small, large)]
    for index in range(len(xs)-1):
        left, right = differences[index], differences[index+1]
        if left == 0:
            return xs[index]
        if left * right < 0:
            fraction = -left / (right-left)
            return xs[index] + fraction * (xs[index+1]-xs[index])
    raise ValueError("no crossing in bracket")
```

`validate_protocol` returns a shallow copy after checking unique odd positive distances, unique probabilities in `(0,1)`, and positive integer shots. `estimate_crossings` groups by distance, sorts by `p`, calls `crossing` for every unordered pair, rejects pairs without a crossing, and returns pair records plus median/min/max.

- [ ] **Step 3: Verify green**

Run the command in Step 1. Expected: all statistical tests PASS.

- [ ] **Step 4: Commit**

```bash
git add research/paper-direction-audit-2026-11-10/surface-code-threshold/protocol.json research/paper-direction-audit-2026-11-10/scripts/surface_code_stats.py research/paper-direction-audit-2026-11-10/tests/test_surface_code_stats.py
git commit -m "test: add surface code statistics kernel"
```

### Task 2: Real Stim/PyMatching runner

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/scripts/run_surface_code_threshold.py`
- Test: `research/paper-direction-audit-2026-11-10/tests/test_surface_code_runner.py`

**Interfaces:**
- Consumes: `validate_protocol`, `wilson_interval`, `estimate_crossings`.
- Produces: `build_circuit(distance:int,p:float,rounds:int|None=None)`, `run_point(distance:int,p:float,shots:int,seed:int)->dict`, `main()->int`.

- [ ] **Step 1: Write failing circuit tests**

```python
import unittest
from run_surface_code_threshold import build_circuit, run_point

class RunnerTests(unittest.TestCase):
    def test_zero_noise_has_no_logical_errors(self):
        circuit = build_circuit(3, 0.0)
        self.assertGreater(circuit.num_detectors, 0)
        result = run_point(3, 0.0, shots=20, seed=7)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["shots"], 20)

    def test_real_small_run_has_verifiable_counts(self):
        result = run_point(3, 0.01, shots=20, seed=11)
        self.assertGreaterEqual(result["errors"], 0)
        self.assertLessEqual(result["errors"], 20)
        self.assertEqual(result["rate"], result["errors"] / 20)
```

Run with the isolated environment. Expected: FAIL because the runner does not exist.

- [ ] **Step 2: Implement the runner**

```python
import stim
import pymatching
from surface_code_stats import validate_protocol, wilson_interval, estimate_crossings


def build_circuit(distance, p, rounds=None):
    if distance % 2 == 0:
        raise ValueError("distance must be odd")
    rounds = distance if rounds is None else rounds
    return stim.Circuit.generated(
        "surface_code:rotated_memory_x", distance=distance, rounds=rounds,
        after_clifford_depolarization=p,
        before_round_data_depolarization=p,
        after_reset_flip_probability=p,
        before_measure_flip_probability=p,
    )


def run_point(distance, p, shots, seed):
    circuit = build_circuit(distance, p)
    model = circuit.detector_error_model(decompose_errors=True)
    matching = pymatching.Matching.from_detector_error_model(model)
    sampler = circuit.compile_detector_sampler()
    syndrome, actual = sampler.sample(shots=shots, separate_observables=True, seed=seed)
    predicted = matching.decode_batch(syndrome)
    errors = sum(bool((actual[index] != predicted[index]).any()) for index in range(shots))
    rate, low, high = wilson_interval(errors, shots)
    return {"distance": distance, "p": p, "shots": shots, "seed": seed,
            "errors": errors, "rate": rate, "wilson95_low": low, "wilson95_high": high,
            "log10_rate": None if rate == 0 else __import__("math").log10(rate)}
```

`main` reads the protocol, runs all 28 points, calls `estimate_crossings` only on nonzero-rate rows, and writes JSON/CSV with dependency versions and the protocol SHA-256.

- [ ] **Step 3: Verify green**

Run both test modules with the isolated Python. Expected: zero-noise and small real-circuit tests PASS.

- [ ] **Step 4: Commit**

```bash
git add research/paper-direction-audit-2026-11-10/scripts/run_surface_code_threshold.py research/paper-direction-audit-2026-11-10/tests/test_surface_code_runner.py
git commit -m "feat: run real surface code monte carlo"
```

### Task 3: Independent verifier and static figure

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/scripts/verify_surface_code_threshold.py`
- Create: `research/paper-direction-audit-2026-11-10/scripts/plot_surface_code_threshold.py`
- Test: `research/paper-direction-audit-2026-11-10/tests/test_surface_code_outputs.py`

**Interfaces:**
- Consumes: `results.json` and `results.csv` produced by Task 2.
- Produces: `verification.json` with zero mismatches and `threshold.svg` tied to the same points.

- [ ] **Step 1: Write failing output tests**

```python
import json
import unittest
from pathlib import Path
from verify_surface_code_threshold import verify_payload
from plot_surface_code_threshold import render_svg

class OutputTests(unittest.TestCase):
    def test_verifier_recomputes_rates(self):
        payload = {"protocol_sha256": "abc", "points": [
            {"distance": 3, "p": 0.005, "shots": 100, "errors": 2,
             "rate": 0.02, "wilson95_low": 0.0, "wilson95_high": 0.1,
             "log10_rate": __import__("math").log10(0.02), "seed": 7}
        ], "crossing_summary": {"crossings": [], "median": None,
                                 "minimum": None, "maximum": None}}
        self.assertEqual(verify_payload(payload, "abc")["mismatches"], [])

    def test_svg_contains_real_coordinates_and_labels(self):
        svg = render_svg([{"distance": 3, "p": 0.005, "rate": 0.02,
                           "wilson95_low": 0.01, "wilson95_high": 0.03}])
        self.assertIn("Logical error rate per shot", svg)
        self.assertIn("0.005", svg)
        self.assertIn("d=3", svg)
```

Expected: FAIL because the output modules do not exist.

- [ ] **Step 2: Implement independent verification and SVG**

`verify_payload(payload, protocol_sha256)` recomputes every rate and Wilson interval with `wilson_interval`, checks `log10_rate`, verifies the payload hash and crossing summary, and returns `{"mismatches": [...]}`. `render_svg(points)` writes a standalone SVG with log-scaled y values, one polyline per distance, circles for real samples and error bars from the stored Wilson interval. No JavaScript or external image is embedded.

- [ ] **Step 3: Verify green**

Run all three test modules. Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add research/paper-direction-audit-2026-11-10/scripts/verify_surface_code_threshold.py research/paper-direction-audit-2026-11-10/scripts/plot_surface_code_threshold.py research/paper-direction-audit-2026-11-10/tests/test_surface_code_outputs.py
git commit -m "test: independently verify surface code outputs"
```

### Task 4: Full run and research integration

**Files:**
- Create: `research/paper-direction-audit-2026-11-10/surface-code-threshold/results.json`
- Create: `research/paper-direction-audit-2026-11-10/surface-code-threshold/results.csv`
- Create: `research/paper-direction-audit-2026-11-10/surface-code-threshold/verification.json`
- Create: `research/paper-direction-audit-2026-11-10/surface-code-threshold/threshold.svg`
- Create: `research/paper-direction-audit-2026-11-10/SURFACE_CODE_BENCHMARK.md`
- Modify: `research/paper-direction-audit-2026-11-10/provider-review.json`
- Modify: `research/paper-direction-audit-2026-11-10/VALIDATION_LOG.md`

- [ ] **Step 1: Execute the full protocol**

Run the isolated Python runner with 20,000 shots per point. Expected: 28 result rows and no fallback data.

- [ ] **Step 2: Independently verify and render**

Run the independent verifier and SVG renderer. Expected: `mismatches: []`, and all SVG coordinates originate from `results.json`.

- [ ] **Step 3: Update the paper review without overclaiming**

Record the observed threshold estimate and bounds as an exploratory result of this exact protocol, not as a refutation of 1.03% under other noise models. Replace the evidence gap for paper three with a link to the reproducible benchmark and retain the missing-original-simulation caveat.

- [ ] **Step 4: Final validation and commit**

Run all audit tests, the independent verifier, `git diff --check`, and `PYTHONPATH=src python scripts/release_audit.py`. Expected: tests PASS, zero mismatches, no whitespace or release-audit failures. Commit and push the completed benchmark.
