import tempfile
import unittest
from pathlib import Path

from garden_ecosystem.context import (
    IntervalCache, ToolOutputGovernor, UsageAnchor, estimate_tokens, resolve_budget,
)
from garden_ecosystem.errors import BudgetExceeded
from garden_ecosystem.security import stable_hash


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.messages = [{"role": "user", "content": "检查引力"}]
        self.anchor = UsageAnchor("m", stable_hash(self.messages), 20)

    def test_anchor_requires_integer_tokens(self):
        with self.assertRaises(ValueError):
            UsageAnchor("m", "prefix", 1.5)

    def test_measured_anchor_must_match_model_and_exact_prefix(self):
        self.assertEqual(resolve_budget(self.messages, "m", 100, 40, self.anchor).source, "measured")
        self.assertEqual(resolve_budget(self.messages, "m", 100, 40,
            UsageAnchor("m", "wrong", 1)).source, "estimate")
        self.assertEqual(resolve_budget(self.messages, "other", 100, 40, self.anchor).source, "estimate")
        changed = self.messages + [{"role": "assistant", "content": "new"}]
        self.assertEqual(resolve_budget(changed, "m", 100, 40, self.anchor).source, "estimate")

    def test_budget_clamps_and_rejects_insufficient_space(self):
        report = resolve_budget(self.messages, "m", 100, 80, self.anchor, reserve=2)
        self.assertEqual(report.tokens, 78)
        self.assertTrue(report.tokens < 80)
        with self.assertRaises(BudgetExceeded):
            resolve_budget(self.messages, "m", 25, 40, self.anchor, reserve=2, minimum=8)

    def test_unknown_window_does_not_invent_measurement(self):
        report = resolve_budget(self.messages, "m", None, 40, self.anchor)
        self.assertEqual(report.tokens, 40)
        self.assertEqual(report.source, "configured")
        self.assertIsNone(report.available)

    def test_invalid_numbers_rejected(self):
        with self.assertRaises(ValueError):
            resolve_budget(self.messages, "m", 0, 40)
        with self.assertRaises(ValueError):
            resolve_budget(self.messages, "m", 100, float("nan"))
        with self.assertRaises(ValueError):
            resolve_budget(self.messages, "m", 100, 40, tools=-1)

    def test_cjk_and_latin_are_conservatively_estimated(self):
        self.assertEqual(estimate_tokens("引力"), 2)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens("引力ab"), 3)

    def test_tool_output_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "result.txt").write_text("x" * 100, encoding="utf-8")
            governor = ToolOutputGovernor(root, inline_limit=20, reference_threshold=60)
            self.assertEqual(governor.govern("small")["kind"], "raw")
            excerpt = governor.govern("x" * 40)
            self.assertEqual(excerpt["kind"], "excerpt")
            self.assertEqual(excerpt["omitted_chars"], 20)
            reference = governor.govern("x" * 100, "result.txt")
            self.assertEqual(reference["kind"], "reference")
            self.assertEqual(reference["chars"], 100)
            self.assertEqual(governor.summary("a summary")["kind"], "summary")

    def test_long_output_requires_real_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            governor = ToolOutputGovernor(directory, inline_limit=1, reference_threshold=2)
            with self.assertRaises(ValueError):
                governor.govern("too long")

    def test_tiny_excerpt_does_not_duplicate_full_output(self):
        with tempfile.TemporaryDirectory() as directory:
            governor = ToolOutputGovernor(directory, inline_limit=1, reference_threshold=2)
            excerpt = governor.govern("ab")
            self.assertEqual(excerpt["omitted_chars"], 2)
            self.assertNotIn("ab", excerpt["text"])

    def test_path_traversal_and_absolute_paths_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            governor = ToolOutputGovernor(directory)
            for candidate in ["../secret", "/etc/passwd", "folder/../../secret"]:
                with self.subTest(candidate=candidate):
                    with self.assertRaises(ValueError):
                        governor.read_interval(candidate)

    def test_interval_cache_reuses_content_and_detects_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.txt"
            path.write_text("0123456789", encoding="utf-8")
            cache = IntervalCache(directory)
            first = cache.get("note.txt", 2, 5)
            second = cache.get("note.txt", 2, 5)
            self.assertEqual(first["text"], "234")
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            path.write_text("abcdefghij", encoding="utf-8")
            changed = cache.get("note.txt", 2, 5)
            self.assertEqual(changed["text"], "cde")
            self.assertFalse(changed["cache_hit"])


if __name__ == "__main__":
    unittest.main()
