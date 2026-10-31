"""Behavior checks for Sprig 2; run with python3 -m unittest discover -s tests."""

import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from sprig import Interpreter, Parser, SprigError, tokenize


ROOT = Path(__file__).resolve().parents[1]


class SprigTests(unittest.TestCase):
    def run_program(self, source, interpreter=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            (interpreter or Interpreter()).run(textwrap.dedent(source))
        return output.getvalue()

    def test_values_and_precedence(self):
        self.assertEqual(self.run_program('''\
            # Comments and blank lines are allowed.

            print(2 + 3 * 4, (2 + 3) * 4, 10 - 3 - 2, 5 / 2, -5 % 3)
            print("hello " + "Sprig", "and", true, false, nil)
            print(not 1 == 2, true or false and false, true == 1)
        '''), "14 20 5 2.5 1\nhello Sprig and true false nil\ntrue true false\n")

    def test_short_circuit(self):
        self.assertEqual(self.run_program('''\
            print(false and missing, true or 1 / 0 == 0)
            let count = 0
            fn visit():
                count = count + 1
                return true
            end
            print(true and visit(), false or visit(), count)
        '''), "false true\ntrue true 2\n")

    def test_booleans_are_not_numbers_or_truthy_values(self):
        for source in ["print(true + 1)", "print(-false)",
                       "print(true < 1)", "print(not 0)",
                       "print(true and 1)", "print(false or 0)",
                       "when 1:\nend", "while 0:\nend"]:
            with self.subTest(source=source), self.assertRaises(SprigError):
                self.run_program(source)

    def test_nested_blocks_and_assignment(self):
        self.assertEqual(self.run_program('''\
            let total = 0
            let n = 0
            while n < 3:
                when n == 1:
                    total = total + 10
                otherwise:
                    repeat 2:
                        total = total + 1
                    end
                end
                n = n + 1
            end
            print(total, n)
        '''), "14 3\n")

    def test_repeat_evaluates_count_once(self):
        self.assertEqual(self.run_program('''\
            let n = 3
            let total = 0
            repeat n:
                total = total + 1
                n = 0
            end
            repeat 0:
                print("unreachable")
            end
            print(total)
        '''), "3\n")
        for count in ["true", "-1", "2.5", '"2"']:
            with self.subTest(count=count), self.assertRaises(SprigError):
                self.run_program(f"repeat {count}:\nend")

    def test_recursion(self):
        self.assertEqual(self.run_program('''\
            fn factorial(n):
                when n <= 1:
                    return 1
                end
                return n * factorial(n - 1)
            end
            print(factorial(6))
        '''), "720\n")

    def test_lexical_scope_and_closure_assignment(self):
        self.assertEqual(self.run_program('''\
            let value = 100
            fn make_counter(value):
                fn next():
                    value = value + 1
                    return value
                end
                return next
            end
            let counter = make_counter(0)
            fn call_counter():
                let value = 900
                return counter()
            end
            print(counter(), call_counter(), value)
        '''), "1 2 100\n")

    def test_return_and_function_errors(self):
        self.assertEqual(self.run_program('''\
            fn early():
                repeat 3:
                    return
                end
                print("unreachable")
            end
            fn empty():
            end
            print(early(), empty())
        '''), "nil nil\n")
        for source in ["fn f(x):\nend\nf()", "let x = 1\nx()",
                       "fn f(x, x):\nend", "return 1"]:
            with self.subTest(source=source), self.assertRaises(SprigError):
                self.run_program(source)

    def test_variables_and_persistent_environment(self):
        interpreter = Interpreter()
        self.run_program("let score = 1", interpreter)
        self.assertEqual(self.run_program("score = score + 2\nprint(score)",
                                          interpreter), "3\n")
        for source in ["print(missing)", "missing = 1",
                       "let score = 1\nlet score = 2"]:
            with self.subTest(source=source), self.assertRaises(SprigError):
                self.run_program(source)
        with self.assertRaisesRegex(SprigError, r"(?i)line 2"):
            self.run_program("# first line\nprint(missing)")

    def test_parse_errors_precede_execution(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SprigError):
            Interpreter().run('print("must not run")\nwhen false:\nlet = 1\nend')
        self.assertEqual(output.getvalue(), "")
        for source in ["print(1 < 2 < 3)", "when true:\nprint(1)",
                       "print(@)", 'print("unterminated)', "end",
                       "let when = 1", "print(1) print(2)", "(x) = 1",
                       "print(1 + not true)"]:
            with self.subTest(source=source), self.assertRaises(SprigError):
                Parser(tokenize(source)).parse()

    def test_example_programs(self):
        examples = sorted((ROOT / "examples").glob("*.sprig"))
        errors = sorted((ROOT / "examples" / "errors").glob("*.sprig"))
        self.assertGreaterEqual(len(examples), 10)
        self.assertGreaterEqual(len(errors), 3)
        for path in examples:
            with self.subTest(program=path.name):
                self.assertEqual(self.run_program(path.read_text()),
                                 path.with_suffix(".out").read_text())
        for path in errors:
            with self.subTest(program=path.name):
                with self.assertRaises(SprigError) as error:
                    self.run_program(path.read_text())
                self.assertIn(path.with_suffix(".err").read_text().strip(), str(error.exception))

    def test_cli(self):
        def cli(*args):
            return subprocess.run([sys.executable, "-m", "sprig", *args],
                                  cwd=ROOT, text=True, capture_output=True)

        self.assertIn("Sprig 2.0", cli("--version").stdout)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "demo.sprig"
            path.write_text('print("hello")\n')
            result = cli(str(path))
            self.assertEqual((result.returncode, result.stdout, result.stderr),
                             (0, "hello\n", ""))
            result = cli("--ast", str(path))
            self.assertEqual(result.returncode, 0)
            self.assertNotEqual(result.stdout, "hello\n")
            path.write_text("print(1 / 0)\n")
            result = cli(str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Division by zero", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_repl_blocks_echo_reset_and_error_recovery(self):
        source = '''\
let total = 0
repeat 2:
    when true: # Nested blocks need their own end.
        total = total + 1
    end
end
total
"end"
missing
2 + 3
:reset
total
true and not false
:quit
'''
        result = subprocess.run([sys.executable, "-m", "sprig"], cwd=ROOT,
                                input=source, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        for value in ["2", "end", "5", "true"]:
            self.assertIn(f"sprig> {value}\n", result.stdout)
        self.assertIn("Undefined name 'missing'", result.stderr)
        self.assertIn("Undefined name 'total'", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        result = subprocess.run([sys.executable, "-m", "sprig"], cwd=ROOT,
                                input="repeat 2:\nprint(1)\n", text=True,
                                capture_output=True, timeout=5)
        self.assertIn("Unfinished block", result.stderr)
        self.assertNotIn("1\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
