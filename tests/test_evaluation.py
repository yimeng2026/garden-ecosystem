import unittest

from garden_ecosystem.evaluation import (
    DIMENSIONS, Domain, EvaluationItem, SharedWorld, aggregate, scenario_report,
)


def scores(value):
    return {name: value for name in DIMENSIONS}


class EvaluationTests(unittest.TestCase):
    def test_all_seven_domains_are_explicit(self):
        self.assertEqual({domain.value for domain in Domain},
                         {"mcp", "search", "terminal", "swe", "android", "web", "os"})

    def test_domain_macro_average_does_not_weight_by_sample_count(self):
        items = [EvaluationItem(Domain.MCP, "ref", "pred", scores(80)),
                 EvaluationItem(Domain.MCP, "ref2", "pred2", scores(60)),
                 EvaluationItem(Domain.WEB, "ref3", "pred3", scores(100))]
        result = aggregate(items)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["domains"]["mcp"]["overall"], 70)
        self.assertEqual(result["macro_average"]["overall"], 85)

    def test_empty_report_has_no_fake_score(self):
        result = aggregate([])
        self.assertEqual(result["domains"], {})
        self.assertIsNone(result["macro_average"])

    def test_nonfinite_missing_and_out_of_range_scores_rejected(self):
        for value in [float("nan"), float("inf"), -1, 101]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    EvaluationItem(Domain.MCP, "ref", "pred", scores(value))
        with self.assertRaises(ValueError):
            EvaluationItem(Domain.MCP, "ref", "pred", {"format": 100})

    def test_shared_world_is_permutation_independent(self):
        actions = {"b": {"observe": {"x": 2}, "message": "from-b"},
                   "a": {"observe": {"x": 1}, "message": "from-a"}}
        first = SharedWorld(["a", "b"]).step(actions, seed=7)
        second = SharedWorld(["b", "a"]).step(dict(reversed(list(actions.items()))), seed=7)
        self.assertEqual(first["state_hash"], second["state_hash"])
        self.assertEqual(first["version"], 1)
        self.assertEqual([message["from"] for message in first["messages"]], ["a", "b"])

    def test_unknown_agent_cannot_change_shared_world(self):
        world = SharedWorld(["a"])
        with self.assertRaises(ValueError):
            world.step({"b": {"message": "intruder"}})
        self.assertEqual(world.version, 0)

    def test_same_seed_is_reproducible_and_report_is_not_prediction(self):
        factory = lambda: SharedWorld(["a", "b"])
        actions = {"a": {"observe": {"x": 1}}, "b": {"observe": {"x": 2}}}
        first = scenario_report(factory, [1, 2], actions)
        second = scenario_report(factory, [1, 2], actions)
        self.assertEqual(first, second)
        self.assertIsNone(first["prediction_probability"])
        self.assertEqual([item["seed"] for item in first["scenarios"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
