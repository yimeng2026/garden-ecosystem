"""Contracts for assembling verification only from a fully successful command log."""

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent


def load_module():
    spec = importlib.util.spec_from_file_location("run_verification", ROOT / "run_verification.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerificationLogReuseTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.assertTrue(hasattr(self.module, "parse_completed_log"), "Completed-log parser is missing")
        self.commands = [("first", ["python", "first.py"], 10), ("second", ["python", "second.py"], 20)]
        self.valid = "$ first: python first.py\nfirst output\nexit_code=0\n$ second: python second.py\nsecond output\nexit_code=0\n"

    def test_complete_unique_zero_log_is_accepted(self):
        rows = self.module.parse_completed_log(self.valid, self.commands)
        self.assertEqual(rows, [
            {"label": "first", "command": ["python", "first.py"], "exit_code": 0},
            {"label": "second", "command": ["python", "second.py"], "exit_code": 0},
        ])

    def test_nonzero_exit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonzero"):
            self.module.parse_completed_log(self.valid.replace("exit_code=0\n$ second", "exit_code=7\n$ second"), self.commands)

    def test_missing_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            self.module.parse_completed_log("$ first: python first.py\nexit_code=0\n", self.commands)

    def test_duplicate_label_is_rejected(self):
        duplicate = self.valid + "$ first: python first.py\nduplicate\nexit_code=0\n"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.module.parse_completed_log(duplicate, self.commands)

    def test_same_label_with_distinct_commands_is_accepted(self):
        commands = [("visual_hash_binding", ["python", "first.py"], 10), ("visual_hash_binding", ["python", "second.py"], 20)]
        log = "$ visual_hash_binding: python first.py\nfirst\nexit_code=0\n$ visual_hash_binding: python second.py\nsecond\nexit_code=0\n"
        rows = self.module.parse_completed_log(log, commands)
        self.assertEqual([row["command"] for row in rows], [["python", "first.py"], ["python", "second.py"]])

    def test_nested_suite_uses_exit_before_next_top_level_command(self):
        log = "$ first: python first.py\n$ nested: python child.py\nchild output\nexit_code=0\nsuite output\nexit_code=0\n$ second: python second.py\nsecond output\nexit_code=0\n"
        rows = self.module.parse_completed_log(log, self.commands)
        self.assertEqual([row["exit_code"] for row in rows], [0, 0])

    def test_command_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "command mismatch"):
            self.module.parse_completed_log(self.valid.replace("python second.py", "python other.py"), self.commands)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
