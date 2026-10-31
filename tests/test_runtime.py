"""Black-box tests of Sprig programs, independent of AST implementation details."""

import io
import unittest

from sprig.errors import SprigError
from sprig.interpreter import Interpreter
from sprig.runner import run_source


class RuntimeTests(unittest.TestCase):
    def run_program(self, source, *, stdin="", args=None, max_steps=None):
        output = io.StringIO()
        interpreter = Interpreter(
            stdout=output,
            stdin=io.StringIO(stdin),
            args=args,
            max_steps=max_steps,
        )
        run_source(source, interpreter=interpreter, filename="test.sprig")
        return output.getvalue(), interpreter

    def assert_program(self, source, expected):
        self.assertEqual(self.run_program(source)[0], expected)

    def assert_language_error(self, source, message=None):
        with self.assertRaises(SprigError) as raised:
            self.run_program(source)
        if message:
            self.assertIn(message.lower(), str(raised.exception).lower())
        return raised.exception

    def test_arithmetic_precedence_and_associativity(self):
        self.assert_program(
            'print(8 + 2 * 3, (8 + 2) * 3, 10 - 3 - 2, -2 * 4, 5 / 2, 7 % 3)\n',
            "14 30 5 -8 2.5 1\n",
        )

    def test_variable_declaration_and_assignment(self):
        self.assert_program('let score = 14\nscore = score + 1\nprint(score)', "15\n")

    def test_literals_and_print_return_value(self):
        self.assert_program('print(true, false, nil, print())\n', "\ntrue false nil nil\n")

    def test_string_escapes_and_concatenation(self):
        self.assert_program('print("hi" + " there")\nprint("a\\nb\\t\\\"c\\\"\\\\")\n', 'hi there\na\nb\t"c"\\\n')

    def test_numeric_equality_and_distinct_kinds(self):
        self.assert_program('print(1 == 1.0, true == 1, nil == false, "1" == 1, 2 != 3)\n', 'true false false false true\n')

    def test_strict_boolean_logic_and_precedence(self):
        self.assert_program('print(not 1 == 2, true or false and false, not false and true)\n', 'true true true\n')

    def test_logical_operators_short_circuit(self):
        self.assert_program('print(false and missing, true or missing)\n', 'false true\n')

    def test_condition_branches(self):
        self.assert_program('let x = 2\nwhen x == 1:\n print("first")\nelif x == 2:\n print("second")\notherwise:\n print("last")\nend\n', 'second\n')

    def test_condition_without_otherwise(self):
        self.assert_program('when false:\n print("no")\nend\nprint("yes")\n', 'yes\n')

    def test_blocks_share_scope(self):
        self.assert_program('when true:\n let score = 7\nend\nprint(score)\n', '7\n')

    def test_while_break_and_continue(self):
        self.assert_program('let n = 0\nlet total = 0\nwhile true:\n n = n + 1\n when n == 2:\n  continue\n end\n when n == 5:\n  break\n end\n total = total + n\nend\nprint(total)\n', '8\n')

    def test_for_range_and_reused_loop_variable(self):
        self.assert_program('let n = 99\nlet total = 0\nfor n in range(1, 5):\n total = total + n\nend\nprint(total, n)\n', '10 4\n')

    def test_for_string_and_snapshot_list_iteration(self):
        self.assert_program('for ch in "ab":\n print(ch)\nend\nlet xs = [1, 2]\nfor item in xs:\n append(xs, item + 2)\nend\nprint(xs)\n', 'a\nb\n[1, 2, 3, 4]\n')

    def test_functions_parameters_and_return(self):
        self.assert_program('fn add(a, b):\n return a + b\nend\nprint(add(3, 4))\n', '7\n')

    def test_functions_return_nil_when_no_value(self):
        self.assert_program('fn empty():\n return\nend\nfn also_empty():\n let x = 1\nend\nprint(empty(), also_empty())\n', 'nil nil\n')

    def test_recursion(self):
        self.assert_program('fn factorial(n):\n when n <= 1:\n  return 1\n end\n return n * factorial(n - 1)\nend\nprint(factorial(6))\n', '720\n')

    def test_local_shadowing_and_enclosing_assignment(self):
        self.assert_program('let x = 10\nfn local():\n let x = 20\n return x\nend\nfn change():\n x = x + 1\nend\nprint(local(), x)\nchange()\nprint(x)\n', '20 10\n11\n')

    def test_closure_survives_return(self):
        self.assert_program('fn counter():\n let count = 0\n fn next():\n  count = count + 1\n  return count\n end\n return next\nend\nlet next = counter()\nprint(next(), next())\n', '1 2\n')

    def test_lexical_rather_than_caller_scope(self):
        self.assert_program('let x = "global"\nfn read():\n return x\nend\nfn caller():\n let x = "local"\n return read()\nend\nprint(caller())\n', 'global\n')

    def test_return_exits_nested_loop(self):
        self.assert_program('fn first():\n for item in [4, 5]:\n  return item\n end\nend\nprint(first())\n', '4\n')

    def test_list_aliases_indexing_mutation_and_concatenation(self):
        self.assert_program('let xs = [1, 2]\nlet alias = xs\nalias[-1] = 9\nappend(xs, 3)\nprint(xs, pop(xs), len(xs), xs + [4])\n', '[1, 9] 3 2 [1, 9, 4]\n')

    def test_string_indexing_and_list_equality(self):
        self.assert_program('print("sprig"[-1], [1, [2]] == [1.0, [2]], [true] == [1])\n', 'g true false\n')

    def test_cyclic_list_format_and_equality_terminate(self):
        result, _ = self.run_program('let xs = []\nappend(xs, xs)\nprint(xs, xs == xs)\nlet ys = []\nappend(ys, ys)\nprint(xs == ys)\n')
        self.assertIn('true', result)
        self.assertLess(len(result), 200)

    def test_input_and_conversion(self):
        output, _ = self.run_program('let name = input("Name: ")\nprint("Hi", name, number("2.5") + 1, str(false))\n', stdin='Ada\n')
        self.assertEqual(output, 'Name: Hi Ada 3.5 false\n')

    def test_builtin_types(self):
        self.assert_program('print(type(1), type("x"), type(true), type(nil), type([]))\n', 'number string boolean nil list\n')

    def test_function_identity_and_type(self):
        self.assert_program('fn f():\nend\nfn g():\nend\nlet alias = f\nprint(f == alias, f == g, type(f), type(print))\n', 'true false function function\n')

    def test_local_builtin_shadowing(self):
        self.assert_program('fn f():\n let len = 7\n return len\nend\nprint(f(), len("abc"))\n', '7 3\n')

    def test_nested_loops_keep_control_signals_local(self):
        self.assert_program('let count = 0\nfor outer in range(3):\n for inner in range(5):\n  when inner == 1:\n   break\n  end\n  count = count + 1\n end\nend\nprint(count)\n', '3\n')

    def test_range_forms(self):
        self.assert_program('print(range(3), range(2, 5), range(5, 0, -2), range(0))\n', '[0, 1, 2] [2, 3, 4] [5, 3, 1] []\n')

    def test_script_arguments(self):
        output, _ = self.run_program('print(args)\n', args=['one', '--two'])
        self.assertEqual(output, '["one", "--two"]\n')

    def test_environment_persists_across_runs(self):
        output, interpreter = self.run_program('let n = 2\n')
        self.assertEqual(output, '')
        run_source('n = n + 3\nprint(n)\n', interpreter=interpreter)
        self.assertEqual(interpreter.stdout.getvalue(), '5\n')

    def test_runtime_error_source_location(self):
        error = self.assert_language_error('let x = 1\nprint(1 / 0)\n')
        self.assertEqual(error.line, 2)
        self.assertGreaterEqual(error.column, 1)

    def test_invalid_operations_raise_language_errors(self):
        cases = [
            'print(missing)', 'missing = 1', 'let x = 1\nlet x = 2',
            'print(1 / 0)', 'print(1 % 0)', 'print("x" + 1)',
            'print(true + 1)', 'print(-true)', 'print("a" < "b")',
            'when 1:\nend', 'while nil:\nend', 'print(not 1)',
            'print(true and 1)', 'print(false or 1)', 'print(1())',
            'fn f(x):\n return x\nend\nf()', 'len(1)', 'len()',
            'append("x", 1)', 'pop([])', 'range(1, 2, 0)',
            'range(true)', 'range(3.0)', 'range(100001)', 'number(true)',
            'number("invalid")', 'number("inf")', 'number("1e309")', 'input()',
            'print([1][true])', 'print([1][1.0])', 'print([1][5])',
            'let s = "a"\ns[0] = "b"', 'for x in 5:\nend',
            'print = 1',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assert_language_error(source)

    def test_illegal_control_flow_is_rejected(self):
        for source in ['return 1', 'break', 'continue', 'while false:\n fn f():\n  break\n end\nend']:
            with self.subTest(source=source):
                self.assert_language_error(source)

    def test_step_limit_stops_infinite_loop(self):
        with self.assertRaises(SprigError):
            self.run_program('while true:\nend\n', max_steps=50)

    def test_deep_recursion_is_a_language_error(self):
        self.assert_language_error('fn recurse():\n return recurse()\nend\nrecurse()\n')

    def test_assignment_rhs_cannot_leak_host_index_error(self):
        self.assert_language_error('let xs = [1]\nfn remove():\n pop(xs)\n return 5\nend\nxs[0] = remove()\n')

    def test_large_literals_and_conversions_are_language_errors(self):
        digits = '9' * 5000
        self.assert_language_error('print(' + digits + ')\n')
        self.assert_language_error('print(number("' + digits + '"))\n')

    def test_deep_expression_is_a_language_error(self):
        self.assert_language_error('print(' + '(' * 1500 + '1' + ')' * 1500 + ')\n')

    def test_deep_list_format_and_equality_are_language_errors(self):
        self.assert_language_error('let xs = []\nfor n in range(1500):\n xs = [xs]\nend\nprint(xs)\n')
        self.assert_language_error('let xs = []\nlet ys = []\nfor n in range(1500):\n xs = [xs]\n ys = [ys]\nend\nprint(xs == ys)\n')


if __name__ == '__main__':
    unittest.main()
