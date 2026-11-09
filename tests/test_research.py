import unittest

from garden_ecosystem.research import (
    ParameterRecord, Preregistration, PreregistrationError,
)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.registration = Preregistration({"hypothesis": "H1", "candidate_domain": [1, 2]})

    def test_freeze_is_content_addressed(self):
        digest = self.registration.freeze()
        self.assertEqual(len(digest), 64)
        self.assertEqual(self.registration.freeze(), digest)
        self.assertEqual(self.registration.frozen_hash, digest)

    def test_exported_payload_cannot_mutate_frozen_content(self):
        self.registration.freeze()
        exported = self.registration.payload
        exported["hypothesis"] = "changed"
        self.assertEqual(self.registration.payload["hypothesis"], "H1")

    def test_observations_append_only_after_freeze(self):
        with self.assertRaises(PreregistrationError):
            self.registration.append_observation({"result": 1})
        self.registration.freeze()
        self.registration.append_observation({"result": 1})
        self.registration.append_observation({"result": 2})
        self.assertEqual(len(self.registration.observations), 2)
        self.assertEqual(self.registration.observations[0]["result"], 1)

    def test_negative_result_requires_reason(self):
        with self.assertRaises(ValueError):
            self.registration.negative_result("candidate-a", "", "test-log")
        result = self.registration.negative_result("candidate-a", "fails invariant", "test-log")
        self.assertEqual(result.reason, "fails invariant")

    def test_parameter_origin_is_explicit(self):
        record = ParameterRecord("M_Pl", "calibrated", "external scale")
        self.assertEqual(record.origin, "calibrated")
        with self.assertRaises(ValueError):
            ParameterRecord("x", "proven", "unsupported origin")

    def test_snapshot_does_not_claim_confirmation(self):
        self.registration.freeze()
        snapshot = self.registration.snapshot()
        self.assertNotIn("confirmed", snapshot)
        self.assertIn("observations", snapshot)


if __name__ == "__main__":
    unittest.main()
