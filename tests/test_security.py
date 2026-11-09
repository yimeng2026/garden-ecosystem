import unittest

from garden_ecosystem.security import redact, stable_hash


class SecurityTests(unittest.TestCase):
    def test_redacts_values_without_empty_replacement(self):
        self.assertEqual(redact("token=abc", ["abc", ""]), "token=[redacted]")

    def test_redacts_json_escaped_secret(self):
        self.assertNotIn("line", redact('{"key":"a\\nb"}', ["a\nb"]))

    def test_stable_hash_is_order_independent_for_mapping_keys(self):
        self.assertEqual(stable_hash({"b": 1, "a": 2}), stable_hash({"a": 2, "b": 1}))

    def test_stable_hash_rejects_nan(self):
        with self.assertRaises(ValueError):
            stable_hash(float("nan"))


if __name__ == "__main__":
    unittest.main()
