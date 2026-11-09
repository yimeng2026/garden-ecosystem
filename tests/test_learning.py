import unittest

from garden_ecosystem.errors import LearningDisabled
from garden_ecosystem.learning import LearningLedger


class LearningTests(unittest.TestCase):
    def test_learning_is_disabled_by_default(self):
        with self.assertRaises(LearningDisabled):
            LearningLedger().record({"text": "keep this", "kind": "guideline"})

    def test_disabled_learning_cannot_evaluate(self):
        with self.assertRaises(LearningDisabled):
            LearningLedger().evaluate("unknown", helped=True, task="a", date="2026-11-09")

    def test_two_independent_help_events_activate(self):
        ledger = LearningLedger(enabled=True)
        item = ledger.record({"text": "run checks", "kind": "guideline"})
        ledger.evaluate(item.id, helped=True, task="a", date="2026-11-09")
        self.assertEqual(item.status, "tentative")
        ledger.evaluate(item.id, helped=True, task="b", date="2026-11-10")
        self.assertEqual(item.status, "active")

    def test_same_event_does_not_activate(self):
        ledger = LearningLedger(enabled=True)
        item = ledger.record({"text": "run checks", "kind": "guideline"})
        for _ in range(2):
            ledger.evaluate(item.id, helped=True, task="a", date="2026-11-09")
        self.assertEqual(item.status, "tentative")

    def test_harm_blocks_activation(self):
        ledger = LearningLedger(enabled=True)
        item = ledger.record({"text": "run checks", "kind": "guideline"})
        ledger.evaluate(item.id, helped=True, task="a", date="2026-11-09")
        ledger.evaluate(item.id, helped=True, task="b", date="2026-11-10", harmed=True)
        self.assertEqual(item.status, "tentative")

    def test_retire_and_rollback_keep_history(self):
        ledger = LearningLedger(enabled=True)
        item = ledger.record({"text": "run checks", "kind": "guideline"})
        ledger.evaluate(item.id, helped=True, task="a", date="2026-11-09")
        ledger.evaluate(item.id, helped=True, task="b", date="2026-11-10")
        ledger.retire(item.id, "contradicted")
        self.assertEqual(item.status, "retired")
        ledger.rollback(item.id)
        self.assertEqual(item.status, "active")
        self.assertTrue(item.history)

    def test_executable_content_is_rejected(self):
        ledger = LearningLedger(enabled=True)
        for key in ["code", "command", "shell", "env", "tool", "config", "secret", "api_key"]:
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    ledger.record({"text": "bad", "kind": "guideline", key: "value"})

    def test_nested_executable_content_is_rejected(self):
        with self.assertRaises(ValueError):
            LearningLedger(enabled=True).record({"text": "bad", "kind": "guideline",
                                                "nested": {"command": "rm -rf"}})

    def test_secret_text_is_redacted(self):
        ledger = LearningLedger(enabled=True, secrets=("private-token",))
        item = ledger.record({"text": "contains private-token", "kind": "guideline"})
        self.assertNotIn("private-token", item.text)


if __name__ == "__main__":
    unittest.main()
