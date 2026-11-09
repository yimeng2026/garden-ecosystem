import unittest

from garden_ecosystem.reliability import Action, DecisionType, Guard


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.guard = Guard(secrets=["topsecret"], clock=lambda: 1000)
        self.calls = []

    def executor(self, action):
        self.calls.append(action.target)
        return {"done": True}

    def test_write_is_denied_by_default(self):
        result = self.guard.execute(Action("agent", "write_file", "notes.md"), self.executor)
        self.assertFalse(result["executed"])
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(self.calls, [])

    def test_read_can_execute(self):
        result = self.guard.execute(Action("agent", "read_file", "notes.md"), self.executor)
        self.assertTrue(result["executed"])
        self.assertEqual(self.calls, ["notes.md"])

    def test_modify_is_suggestion_not_permission(self):
        decision = self.guard.check(Action("agent", "write_file", "tests/test_demo.py"))
        self.assertEqual(decision.type, DecisionType.MODIFY)
        self.assertFalse(decision.executable)
        self.assertEqual(decision.suggested.target, "src/demo.py")
        result = self.guard.execute(Action("agent", "write_file", "tests/test_demo.py"), self.executor)
        self.assertFalse(result["executed"])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.guard.check(decision.suggested).type, DecisionType.DENY)

    def test_approval_is_bound_to_action_and_single_use(self):
        action = Action("agent", "deploy", "production")
        self.assertEqual(self.guard.check(action).type, DecisionType.ASK)
        ticket = self.guard.approve(action, ttl_seconds=10)
        wrong = self.guard.execute(Action("agent", "deploy", "production-b"), self.executor, ticket)
        self.assertFalse(wrong["executed"])
        good = self.guard.execute(action, self.executor, ticket)
        self.assertTrue(good["executed"])
        again = self.guard.execute(action, self.executor, ticket)
        self.assertFalse(again["executed"])
        self.assertEqual(self.calls, ["production"])

    def test_expired_ticket_cannot_execute(self):
        clock = [1000]
        guard = Guard(clock=lambda: clock[0])
        action = Action("agent", "deploy", "production")
        ticket = guard.approve(action, ttl_seconds=1)
        clock[0] = 1002
        self.assertFalse(guard.execute(action, self.executor, ticket)["executed"])
        self.assertEqual(self.calls, [])

    def test_ticket_cannot_be_issued_for_allow_or_deny(self):
        with self.assertRaises(ValueError):
            self.guard.approve(Action("agent", "read_file", "a"))
        with self.assertRaises(ValueError):
            self.guard.approve(Action("agent", "write_file", "a"))

    def test_force_push_is_denied(self):
        for command in ["git push --force origin main", "git push -f origin main"]:
            with self.subTest(command=command):
                result = self.guard.execute(Action("agent", "git", command), self.executor)
                self.assertEqual(result["decision"], "DENY")
        self.assertEqual(self.calls, [])

    def test_shell_and_production_delete_are_denied(self):
        self.assertEqual(self.guard.check(Action("agent", "shell", "echo safe")).type, DecisionType.DENY)
        self.assertEqual(self.guard.check(Action("agent", "database", "DROP TABLE users")).type, DecisionType.DENY)

    def test_large_spend_denied_small_spend_asks(self):
        large = Action("agent", "spend", "cloud", {"amount": 1000})
        small = Action("agent", "spend", "cloud", {"amount": 10})
        self.assertEqual(self.guard.check(large).type, DecisionType.DENY)
        self.assertEqual(self.guard.check(small).type, DecisionType.ASK)

    def test_read_path_traversal_denied(self):
        self.assertEqual(self.guard.check(Action("agent", "read_file", "../secret")).type, DecisionType.DENY)
        self.assertEqual(self.guard.check(Action("agent", "read_file", "/etc/passwd")).type, DecisionType.DENY)

    def test_audit_redacts_target(self):
        result = self.guard.execute(Action("agent", "write_file", "topsecret.md"), self.executor)
        self.assertNotIn("topsecret", str(result))
        self.assertNotIn("topsecret", str(self.guard.audit))

    def test_executor_error_is_not_recorded_as_success(self):
        def fail(action):
            raise RuntimeError("topsecret failure")
        result = self.guard.execute(Action("agent", "read_file", "notes.md"), fail)
        self.assertFalse(result["executed"])
        self.assertEqual(result["status"], "error")
        self.assertNotIn("topsecret", str(result))


if __name__ == "__main__":
    unittest.main()
