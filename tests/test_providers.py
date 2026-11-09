import unittest

from garden_ecosystem.providers import (
    FailureKind, ProviderError, ProviderPool, ProviderProfile, scoped_secret,
)


def profile(name, fallbacks=()):
    return ProviderProfile(name, f"model-{name}", f"{name.upper()}_KEY", tuple(fallbacks))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.environment = {"A_KEY": "secret-a", "B_KEY": "secret-b", "C_KEY": "secret-c"}
        self.pool = ProviderPool([profile("a", ["b"]), profile("b", ["c"]), profile("c")], self.environment)

    def test_only_transient_failure_switches_provider_and_redacts_audit(self):
        calls = []
        def transport(current, secret, request):
            calls.append((current.name, secret))
            if current.name == "a":
                raise ProviderError(FailureKind.RATE_LIMIT, "secret-a was throttled")
            return {"content": "ok"}
        self.assertEqual(self.pool.call({}, transport)["content"], "ok")
        self.assertEqual([name for name, _ in calls], ["a", "b"])
        audit = str(self.pool.audit)
        self.assertNotIn("secret-a", audit)
        self.assertNotIn("secret-b", audit)

    def test_auth_does_not_switch(self):
        calls = []
        def transport(current, secret, request):
            calls.append(current.name)
            raise ProviderError(FailureKind.AUTH, "bad credentials")
        with self.assertRaises(ProviderError) as error:
            self.pool.call({}, transport)
        self.assertEqual(calls, ["a"])
        self.assertEqual(error.exception.kind, FailureKind.AUTH)

    def test_all_non_transient_kinds_do_not_switch(self):
        kinds = [FailureKind.ABORT, FailureKind.INVALID_REQUEST, FailureKind.NOT_FOUND,
                 FailureKind.CONTEXT_OVERFLOW]
        for kind in kinds:
            with self.subTest(kind=kind):
                with self.assertRaises(ProviderError) as error:
                    self.pool.call({}, lambda *_: self._raise(kind))
                self.assertEqual(error.exception.kind, kind)
                self.assertEqual(self.pool.audit[-1]["provider"], "a")

    def _raise(self, kind):
        raise ProviderError(kind, "failure")

    def test_transient_kinds_can_switch(self):
        for kind in [FailureKind.SERVER, FailureKind.TIMEOUT, FailureKind.NETWORK]:
            with self.subTest(kind=kind):
                def transport(current, secret, request):
                    if current.name == "a":
                        raise ProviderError(kind, "temporary")
                    return {"ok": True}
                self.assertTrue(self.pool.call({}, transport)["ok"])

    def test_cycle_is_deduplicated(self):
        pool = ProviderPool([profile("a", ["b"]), profile("b", ["a"])], self.environment)
        attempts = []
        def transport(current, secret, request):
            attempts.append(current.name)
            raise ProviderError(FailureKind.TIMEOUT, "timeout")
        with self.assertRaises(ProviderError):
            pool.call({}, transport)
        self.assertEqual(attempts, ["a", "b"])

    def test_hop_limit(self):
        pool = ProviderPool([profile("a", ["b", "c"]), profile("b"), profile("c")],
                            self.environment, max_hops=1)
        attempts = []
        def transport(current, secret, request):
            attempts.append(current.name)
            raise ProviderError(FailureKind.TIMEOUT, "timeout")
        with self.assertRaises(ProviderError):
            pool.call({}, transport)
        self.assertEqual(attempts, ["a", "b"])

    def test_missing_secret_does_not_switch_or_expose_value(self):
        pool = ProviderPool([profile("missing", ["b"]), profile("b")], self.environment)
        with self.assertRaises(ProviderError) as error:
            pool.call({}, lambda *_: {"unexpected": True})
        self.assertEqual(error.exception.kind, FailureKind.AUTH)
        self.assertIn("MISSING_KEY", str(error.exception))

    def test_empty_pool_rejected(self):
        with self.assertRaises(ProviderError):
            ProviderPool([]).call({}, lambda *_: {})

    def test_scoped_secret_restores_previous_value(self):
        environment = {"KEY": "old"}
        with scoped_secret(environment, "KEY", "new"):
            self.assertEqual(environment["KEY"], "new")
        self.assertEqual(environment["KEY"], "old")

    def test_scoped_secret_removes_new_value_on_error(self):
        environment = {}
        with self.assertRaises(RuntimeError):
            with scoped_secret(environment, "KEY", "temporary"):
                self.assertEqual(environment["KEY"], "temporary")
                raise RuntimeError("stop")
        self.assertNotIn("KEY", environment)

    def test_unknown_exception_is_not_mislabelled(self):
        with self.assertRaises(RuntimeError):
            self.pool.call({}, lambda *_: self._raise_runtime())
        self.assertEqual(len(self.pool.audit), 0)

    def _raise_runtime(self):
        raise RuntimeError("programming error")


if __name__ == "__main__":
    unittest.main()
