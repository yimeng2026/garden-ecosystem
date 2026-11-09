import json
import unittest

from garden_ecosystem.errors import CheckpointMismatch
from garden_ecosystem.receipts import (
    CheckpointStore, ExternalToolUnavailable, RunManifest, UnavailableExternalTool,
    VerificationLevel, VerificationReceipt,
)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.manifest = RunManifest.create(project="demo", config={
            "model": "mock", "api_key": "do-not-store", "auth": "do-not-store-auth",
            "nested": {"token": "hide"},
        }, seed=7, clock=lambda: 1000)
        self.store = CheckpointStore(clock=lambda: 1000)

    def test_manifest_has_no_secret_values(self):
        from garden_ecosystem.receipts import public_config
        serialized = json.dumps(public_config({"api_key": "do-not-store",
            "auth": "do-not-store-auth", "nested": {"token": "hide"}}))
        self.assertNotIn("do-not-store", serialized)
        self.assertNotIn("do-not-store-auth", serialized)
        self.assertNotIn("hide", serialized)
        self.assertEqual(self.manifest.seed, 7)
        self.assertEqual(self.manifest.created_at, 1000)

    def test_checkpoint_resumes_only_matching_chain_and_action(self):
        first = self.store.append(self.manifest.run_id, None, {"tool": "read"}, {"value": 1})
        resumed = self.store.resume(self.manifest.run_id, first.hash, {"tool": "read"})
        self.assertEqual(resumed.state, {"value": 1})
        with self.assertRaises(CheckpointMismatch):
            self.store.resume(self.manifest.run_id, "wrong", {"tool": "read"})
        with self.assertRaises(CheckpointMismatch):
            self.store.resume(self.manifest.run_id, first.hash, {"tool": "write"})

    def test_wrong_previous_hash_cannot_extend_chain(self):
        with self.assertRaises(CheckpointMismatch):
            self.store.append(self.manifest.run_id, "not-a-parent", {}, {})

    def test_nonfinite_checkpoint_time_rejected(self):
        store = CheckpointStore(clock=lambda: float("nan"))
        with self.assertRaises(ValueError):
            store.append(self.manifest.run_id, None, {}, {})

    def test_mock_machine_check_is_explicit(self):
        receipt = VerificationReceipt.machine_checked(
            tool="mock-lean", version="0", evidence_hash="abc", mock=True)
        self.assertTrue(receipt.mock)
        self.assertEqual(receipt.level, VerificationLevel.MACHINE_CHECKED)

    def test_real_machine_check_requires_attestation(self):
        with self.assertRaises(ValueError):
            VerificationReceipt.machine_checked(tool="lean", version="4", evidence_hash="abc")
        receipt = VerificationReceipt.machine_checked(
            tool="lean", version="4", evidence_hash="abc", attested=True)
        self.assertFalse(receipt.mock)

    def test_direct_constructor_cannot_bypass_attestation(self):
        with self.assertRaises(ValueError):
            VerificationReceipt(VerificationLevel.MACHINE_CHECKED, "lean", "4", "abc")
        with self.assertRaises(ValueError):
            VerificationReceipt(VerificationLevel.EXTERNALLY_VALIDATED, "lab", "1", "abc")

    def test_levels_are_not_an_automatic_truth_ladder(self):
        self.assertNotEqual(VerificationLevel.MACHINE_CHECKED, VerificationLevel.EXTERNALLY_VALIDATED)
        self.assertNotEqual(VerificationLevel.EXECUTED, VerificationLevel.NUMERICALLY_REPRODUCED)

    def test_unavailable_tool_cannot_execute(self):
        tool = UnavailableExternalTool("lean")
        self.assertEqual(tool.health().status, "unavailable")
        with self.assertRaises(ExternalToolUnavailable):
            tool.execute({"tool": "lean"})


if __name__ == "__main__":
    unittest.main()
