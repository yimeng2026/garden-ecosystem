import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from garden_ecosystem.bridge import capabilities, health
from garden_ecosystem.demo import run_demo
from garden_ecosystem.receipts import UnavailableExternalTool


class BridgeTests(unittest.TestCase):
    def test_capabilities_exposes_safe_interface(self):
        result = capabilities()
        self.assertEqual(result["default_policy"], "deny")
        self.assertEqual(result["network"], "injected_only")
        self.assertIn("receipts", result["modules"])

    def test_health_reports_real_unavailable_tools(self):
        result = health([UnavailableExternalTool("lean")])
        self.assertEqual(result["tools"]["lean"]["status"], "unavailable")
        self.assertFalse(result["learning_enabled"])
        self.assertFalse(result["secrets_loaded"])

    def test_offline_demo_composes_all_layers(self):
        report = run_demo()
        self.assertTrue(report["ok"])
        self.assertTrue(report["mock"])
        self.assertTrue(report["offline"])
        self.assertFalse(report["guard"]["executed"])
        self.assertEqual(report["migration"]["status"], "rolled_back")
        self.assertEqual(report["learning"]["enabled"], False)
        self.assertEqual(set(report["evaluation"]["domains"]), set())
        self.assertTrue(report["verification_receipt"]["mock"])
        self.assertEqual(report["external_tool"]["status"], "unavailable")
        self.assertEqual(report["scenario"]["scenario_count"], 2)
        json.dumps(report, allow_nan=False)

    def test_demo_does_not_leak_fake_key(self):
        self.assertNotIn("offline-demo-key-not-a-secret", str(run_demo()))

    def test_module_cli_outputs_valid_json(self):
        root = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(root / "src")
        result = subprocess.run([sys.executable, "-m", "garden_ecosystem"],
                                cwd=root, env=environment, capture_output=True,
                                text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertTrue(report["offline"])


if __name__ == "__main__":
    unittest.main()
