import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from garden_ecosystem.lean import LeanAdapter, _run
from garden_ecosystem.receipts import ExternalToolUnavailable, VerificationLevel


class LeanTests(unittest.TestCase):
    def test_default_runner_decodes_utf8_stdout_and_stderr(self):
        child = (
            "import sys; "
            "sys.stdout.buffer.write('Lean ‘proof’'.encode('utf-8')); "
            "sys.stderr.buffer.write('诊断'.encode('utf-8'))"
        )
        result = _run([sys.executable, "-c", child], 3.0)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "Lean ‘proof’")
        self.assertEqual(result.stderr, "诊断")

    def test_missing_executable_is_unavailable(self):
        adapter = LeanAdapter(executable="definitely-not-a-real-lean")
        health = adapter.health()
        self.assertEqual(health.status, "unavailable")
        with self.assertRaises(ExternalToolUnavailable):
            adapter.execute({"operation": "health"})

    def test_successful_real_version_contract(self):
        commands = []
        def successful(command, timeout):
            commands.append(command)
            return SimpleNamespace(returncode=0, stdout="Lean (version 4.31.0, x86_64)", stderr="")
        adapter = LeanAdapter(executable="lean", runner=successful)
        with patch("garden_ecosystem.lean.shutil.which", return_value="lean"):
            self.assertEqual(adapter.health().status, "available")
            receipt = adapter.execute({"operation": "health"})
        self.assertEqual(commands, [["lean", "--version"], ["lean", "--version"]])
        self.assertEqual(receipt.level, VerificationLevel.EXECUTED)
        self.assertFalse(receipt.attested)
        self.assertTrue(receipt.mock)
        self.assertEqual(receipt.version, "4.31.0")

    def test_nonzero_and_empty_output_are_degraded(self):
        for result in [SimpleNamespace(returncode=1, stdout="error", stderr=""),
                       SimpleNamespace(returncode=0, stdout="", stderr=""),
                       SimpleNamespace(returncode=0, stdout="not a Lean banner", stderr="")]:
            with self.subTest(result=result):
                adapter = LeanAdapter(executable="lean", runner=lambda *args: result)
                with patch("garden_ecosystem.lean.shutil.which", return_value="lean"):
                    self.assertEqual(adapter.health().status, "degraded")

    def test_timeout_is_degraded(self):
        def timeout(command, timeout):
            raise subprocess.TimeoutExpired(command, timeout)
        adapter = LeanAdapter(executable="lean", runner=timeout)
        with patch("garden_ecosystem.lean.shutil.which", return_value="lean"):
            self.assertEqual(adapter.health().status, "degraded")

    def test_other_operations_are_never_allowed(self):
        adapter = LeanAdapter(executable="lean", runner=lambda *args: SimpleNamespace(
            returncode=0, stdout="Lean (version 4.31.0, x86_64)", stderr=""))
        with patch("garden_ecosystem.lean.shutil.which", return_value="lean"):
            with self.assertRaises(ValueError):
                adapter.execute({"operation": "compile", "file": "Proof.lean"})

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ValueError):
            LeanAdapter(timeout=0)

    def test_real_probe_is_not_hardcoded(self):
        # This is a real host probe, not proof that Lean exists on every machine.
        self.assertIn(LeanAdapter().health().status, {"available", "degraded", "unavailable"})


if __name__ == "__main__":
    unittest.main()
