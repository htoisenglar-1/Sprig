"""Regression checks found during an independent runtime review."""

import io
import unittest

from sprig.errors import RuntimeFault
from sprig.interpreter import Interpreter
from sprig.runner import run_source


class DefinitionSourceTests(unittest.TestCase):
    def check_definition_fault(self, source, name, line, column):
        interpreter = Interpreter(stdout=io.StringIO())
        run_source(source, interpreter, "definition.sprig")
        with self.assertRaises(RuntimeFault) as caught:
            run_source(f"{name}()\n", interpreter, "caller.sprig")
        error = caught.exception
        self.assertEqual(error.filename, "definition.sprig")
        self.assertEqual(error.source, source)
        self.assertEqual((error.line, error.column), (line, column))
        self.assertIn("definition.sprig:", error.render(error.source, error.filename))

    def test_deep_comparison_points_at_definition_operator(self):
        # Iteration constructs deep values without deeply nested source syntax.
        source = (
            "fn compare():\n"
            "let a = []\n"
            "let b = []\n"
            "for i in range(1500):\n"
            "a = [a]\n"
            "b = [b]\n"
            "end\n"
            "return a == b\n"
            "end\n"
        )
        self.check_definition_fault(source, "compare", 8, 10)

    def test_numeric_overflow_points_at_definition_operator(self):
        source = (
            "fn divide():\n"
            "let huge = 1\n"
            "for i in range(1100):\n"
            "huge = huge * 2\n"
            "end\n"
            "return huge / 1.0\n"
            "end\n"
        )
        self.check_definition_fault(source, "divide", 6, 13)


if __name__ == "__main__":
    unittest.main()
