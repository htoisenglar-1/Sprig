"""I/O failures should stop the CLI cleanly, including interactive mode."""

from contextlib import redirect_stderr
import io
import unittest
from unittest.mock import patch

from sprig.cli import main


class IOTests(unittest.TestCase):
    def test_repl_stream_failure_is_reported(self):
        for error in (OSError("input unavailable"), UnicodeError("output unavailable")):
            with self.subTest(error=error):
                stderr = io.StringIO()
                with patch("sprig.cli.repl", side_effect=error), redirect_stderr(stderr):
                    status = main([])
                self.assertEqual(status, 1)
                self.assertIn("IOError:", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
