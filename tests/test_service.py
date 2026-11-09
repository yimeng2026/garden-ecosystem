import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from garden_ecosystem.receipts import UnavailableExternalTool
from garden_ecosystem.service import Service
from garden_ecosystem.proof import ProofReport
from garden_ecosystem.receipts import VerificationLevel, VerificationReceipt


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = Service(lean=UnavailableExternalTool("lean"))

    def test_lean_health_response(self):
        response = self.service.handle({"id": "one", "action": "lean_health", "params": {}})
        self.assertEqual(response, {"id": "one", "ok": True,
            "result": {"status": "unavailable", "reason": "no configured real adapter for lean"}})

    def test_capabilities_and_health(self):
        capabilities = self.service.handle({"id": "c", "action": "capabilities", "params": {}})
        self.assertIn("lean", capabilities["result"]["modules"])
        self.assertIn("service", capabilities["result"]["modules"])
        self.assertIn("proof", capabilities["result"]["modules"])
        health = self.service.handle({"id": "h", "action": "health", "params": {}})
        self.assertEqual(health["result"]["tools"]["lean"]["status"], "unavailable")

    def test_unavailable_receipt_is_structured_error(self):
        response = self.service.handle_safely({"id": "r", "action": "lean_receipt", "params": {}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["type"], "ExternalToolUnavailable")

    def test_lean_check_returns_structured_proof_report(self):
        receipt = VerificationReceipt(VerificationLevel.MACHINE_CHECKED,
                                      "lean", "4.35.0", "evidence", mock=True)
        expected = ProofReport(True, receipt, "one_add_one_eq_two", "Smoke.lean",
                               False, (), "", "", "source-hash")
        class FakeProof:
            def execute(self, action):
                self.action = action
                return expected
        fake = FakeProof()
        response = Service(proof=fake).handle({"id": "proof", "action": "lean_check",
            "params": {"path": "Smoke.lean", "declaration": "one_add_one_eq_two"}})
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["receipt"]["level"], "machine_checked")
        self.assertEqual(fake.action["operation"], "check_file")

    def test_lean_check_rejects_extra_params(self):
        response = self.service.handle_safely({"id": "bad-proof", "action": "lean_check",
            "params": {"path": "Smoke.lean", "declaration": "one_add_one_eq_two", "command": "lake"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["type"], "ValueError")

    def test_unknown_action_and_bad_params_are_rejected(self):
        unknown = self.service.handle_safely({"id": "bad", "action": "shell", "params": {}})
        self.assertFalse(unknown["ok"])
        self.assertEqual(unknown["error"]["type"], "ValueError")
        for request in [{"action": "health"}, {"id": 1, "action": "health"},
                        {"id": "x", "action": "health", "params": []},
                        {"id": "x", "action": "health", "params": {"operation": "delete"}}]:
            with self.subTest(request=request):
                self.assertFalse(self.service.handle_safely(request)["ok"])

    def test_unexpected_error_does_not_echo_sensitive_message(self):
        class BrokenTool:
            name = "lean"
            def health(self):
                raise RuntimeError("sensitive internal detail")
        response = Service(lean=BrokenTool()).handle_safely({"id": "x", "action": "health", "params": {}})
        self.assertFalse(response["ok"])
        self.assertNotIn("sensitive", response["error"]["message"])

    def test_stdio_round_trip(self):
        root = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(root / "src")
        request = json.dumps({"id": "subprocess", "action": "capabilities", "params": {}})
        result = subprocess.run([sys.executable, "-m", "garden_ecosystem.service"],
                                input=request, text=True, capture_output=True,
                                cwd=root, env=environment, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertTrue(response["ok"])
        self.assertEqual(response["id"], "subprocess")

    def test_invalid_json_and_oversized_stdin(self):
        root = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(root / "src")
        for payload in ["{not json", " " * 16385]:
            with self.subTest(payload_size=len(payload)):
                result = subprocess.run([sys.executable, "-m", "garden_ecosystem.service"],
                                        input=payload, text=True, capture_output=True,
                                        cwd=root, env=environment, timeout=30, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
