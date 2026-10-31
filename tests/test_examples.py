"""The supplied lessons must stay runnable and match their documented output."""

import io
from pathlib import Path
import unittest

from sprig.interpreter import Interpreter
from sprig.runner import run_source


class ExampleTests(unittest.TestCase):
    def test_documented_program_outputs(self):
        expected = {
            "hello": "Hello, Crystal\n14\nGoal reached!\n",
            "arithmetic": "14\n20\n2.5\ntrue\nhello Sprig\n",
            "loops": "0\n1\n2\n1\n3\nthree\n",
            "functions": "120\nnil\n",
            "closures": "1\n2\n1\n",
            "lists": "[2, 4, 6]\n6\n[2, 4]\n2\ntrue\n",
            "input": "Your name: Hello, Ada\n",
            "arguments": "Ada\nAda\nAda\n",
        }
        folder = Path(__file__).resolve().parents[1] / "examples"
        self.assertEqual({p.stem for p in folder.glob("*.sprig")}, set(expected))
        for name, output in expected.items():
            with self.subTest(example=name):
                stdout = io.StringIO()
                interpreter = Interpreter(stdout=stdout, stdin=io.StringIO("Ada\n"), args=["Ada", "3"], max_steps=10000)
                path = folder / f"{name}.sprig"
                run_source(path.read_text(encoding="utf-8"), interpreter, str(path))
                self.assertEqual(stdout.getvalue(), output)
