import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from garden_ecosystem.proof import LeanProofAdapter
from garden_ecosystem.receipts import ExternalToolUnavailable, VerificationLevel


THEOREM = "theorem one_add_one_eq_two : 1 + 1 = 2 := by\n  rfl\n"


class FakeRunner:
    def __init__(self, returncode=0, stdout="one_add_one_eq_two does not depend on any axioms\n", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.commands = []
        self.wrapper = None
        self.wrapper_text = ""

    def __call__(self, command, timeout):
        self.commands.append(command)
        if command[1:] == ["--version"]:
            return SimpleNamespace(returncode=0, stdout="Lean (version 4.35.0, x86_64)", stderr="")
        self.wrapper = Path(command[-1])
        self.wrapper_bytes = self.wrapper.read_bytes()
        self.wrapper_text = self.wrapper.read_text(encoding="utf-8")
        return SimpleNamespace(returncode=self.returncode, stdout=self.stdout, stderr=self.stderr)


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / "Smoke.lean").write_text(THEOREM, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def adapter(self, runner):
        return LeanProofAdapter(self.workspace, executable="lean", runner=runner,
                                resolver=lambda _: "lean")

    def test_minimal_proof_is_machine_checked_and_mock_is_explicit(self):
        runner = FakeRunner()
        report = self.adapter(runner).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertTrue(report.ok)
        self.assertEqual(report.receipt.level, VerificationLevel.MACHINE_CHECKED)
        self.assertFalse(report.depends_on_axioms)
        self.assertEqual(report.axioms, ())
        self.assertTrue(report.receipt.mock)
        self.assertFalse(report.receipt.attested)
        self.assertEqual(report.path, "Smoke.lean")
        self.assertEqual(len(report.source_hash), 64)
        self.assertIn("#print axioms one_add_one_eq_two", runner.wrapper_text)

    def test_temporary_wrapper_is_removed(self):
        runner = FakeRunner()
        self.adapter(runner).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertFalse(runner.wrapper.parent.exists())

    def test_crlf_source_is_not_double_translated_in_wrapper(self):
        source = THEOREM.replace("\n", "\r\n")
        (self.workspace / "Crlf.lean").write_bytes(source.encode("utf-8"))
        runner = FakeRunner()
        self.adapter(runner).execute({
            "operation": "check_file", "path": "Crlf.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertNotIn(b"\r\r\n", runner.wrapper_bytes)
        self.assertEqual(runner.wrapper_bytes,
                         source.encode("utf-8") + b"\n#print axioms one_add_one_eq_two\n")

    def test_comments_and_strings_do_not_trigger_directives(self):
        (self.workspace / "Commented.lean").write_text(
            "-- #eval and sorry are comments\n/- nested /- comment -/ #eval -/\n"
            "def s : String := \"#eval import sorry\"\n"
            "theorem s_eq : s = s := by rfl\n", encoding="utf-8")
        report = self.adapter(FakeRunner()).execute({
            "operation": "check_file", "path": "Commented.lean", "declaration": "s_eq",
        })
        self.assertTrue(report.ok)

    def test_dangerous_sources_are_rejected_before_execution(self):
        sources = [
            "import Foo", "#eval 1", "theorem bad : False := by sorry",
            "axiom bad : False", "unsafe def bad : Nat := 1",
            "set_option maxRecDepth 1000", "run_cmd IO.println \"x\"",
            "macro \"x\" : term => pure 1", "postulate bad : False",
        ]
        for index, source in enumerate(sources):
            with self.subTest(source=source):
                path = self.workspace / f"Bad{index}.lean"
                path.write_text(source, encoding="utf-8")
                runner = FakeRunner()
                with self.assertRaises(ValueError):
                    self.adapter(runner).execute({
                        "operation": "check_file", "path": path.name, "declaration": "bad",
                    })
                self.assertEqual(runner.commands, [])

    def test_path_and_size_boundaries(self):
        (self.workspace / "Smoke.txt").write_text(THEOREM, encoding="utf-8")
        for path in ["../secret.lean", str(self.workspace / "Smoke.lean"), "Smoke.txt", "missing.lean", "."]:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    self.adapter(FakeRunner()).execute({
                        "operation": "check_file", "path": path, "declaration": "one_add_one_eq_two",
                    })
        (self.workspace / "Large.lean").write_text(" " * 65_537, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.adapter(FakeRunner()).execute({
                "operation": "check_file", "path": "Large.lean", "declaration": "one_add_one_eq_two",
            })

    def test_compiler_failure_is_not_machine_checked_and_redacts_paths(self):
        runner = FakeRunner(returncode=1, stdout="", stderr=f"{self.workspace}/private/Check.lean:1: error")
        report = self.adapter(runner).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertFalse(report.ok)
        self.assertEqual(report.receipt.level, VerificationLevel.EXECUTED)
        self.assertNotIn(str(self.workspace), report.stderr)
        self.assertIn("<workspace>", report.stderr)

    def test_unrecognized_axiom_output_is_not_success(self):
        report = self.adapter(FakeRunner(stdout="unrecognized output")).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertFalse(report.ok)
        self.assertIsNone(report.depends_on_axioms)
        self.assertEqual(report.receipt.level, VerificationLevel.EXECUTED)

    def test_reported_axioms_are_retained(self):
        runner = FakeRunner(stdout="one_add_one_eq_two depends on axioms: [propext, Classical.choice]")
        report = self.adapter(runner).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertTrue(report.ok)
        self.assertTrue(report.depends_on_axioms)
        self.assertEqual(report.axioms, ("propext", "Classical.choice"))

    def test_timeout_is_an_execution_failure(self):
        class TimeoutRunner(FakeRunner):
            def __call__(self, command, timeout):
                if command[1:] != ["--version"]:
                    raise subprocess.TimeoutExpired(command, timeout)
                return super().__call__(command, timeout)
        report = self.adapter(TimeoutRunner()).execute({
            "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
        })
        self.assertFalse(report.ok)
        self.assertEqual(report.receipt.level, VerificationLevel.EXECUTED)

    def test_unknown_operation_and_extra_params_are_rejected(self):
        for action in [{"operation": "compile", "path": "Smoke.lean", "declaration": "x"},
                       {"operation": "check_file", "path": "Smoke.lean", "declaration": "x", "command": "lake"}]:
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    self.adapter(FakeRunner()).execute(action)

    def test_unavailable_tool_cannot_compile(self):
        adapter = LeanProofAdapter(self.workspace, executable="definitely-not-real-lean")
        with self.assertRaises(ExternalToolUnavailable):
            adapter.execute({
                "operation": "check_file", "path": "Smoke.lean", "declaration": "one_add_one_eq_two",
            })


if __name__ == "__main__":
    unittest.main()
