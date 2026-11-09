import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import release_audit


class ReleaseAuditTests(unittest.TestCase):
    def test_git_paths_are_decoded_as_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["README.md", "LICENSE", "NOTICE.md", "UPSTREAM.md", "pyproject.toml", "调研.md"]:
                (root / name).write_text("placeholder-free documentation", encoding="utf-8")
            paths = "README.md\nLICENSE\nNOTICE.md\nUPSTREAM.md\npyproject.toml\n调研.md"
            with patch.object(release_audit, "ROOT", root), \
                 patch.object(release_audit.subprocess, "check_output", return_value=paths) as command, \
                 contextlib.redirect_stdout(io.StringIO()):
                release_audit.main()
            self.assertEqual(command.call_args.kwargs.get("encoding"), "utf-8")


if __name__ == "__main__":
    unittest.main()
