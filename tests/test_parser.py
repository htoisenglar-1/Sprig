"""Parser tests inspect trees, independently of the interpreter."""

import unittest

from sprig import ast_nodes as A
from sprig.errors import IncompleteInput, ParseError
from sprig.lexer import Lexer
from sprig.parser import Parser
from sprig.tokens import TokenType as T


def parse(source):
    return Parser(Lexer(source).scan_tokens()).parse()


class ParserTests(unittest.TestCase):
    def expression(self, source):
        return parse(source)[0].expression

    def test_arithmetic_precedence(self):
        expression = self.expression("8 + 2 * 3")
        self.assertEqual(expression.token.kind, T.PLUS)
        self.assertEqual(expression.right.token.kind, T.STAR)

    def test_parentheses_change_precedence(self):
        expression = self.expression("(8 + 2) * 3")
        self.assertEqual(expression.token.kind, T.STAR)
        self.assertEqual(expression.left.token.kind, T.PLUS)

    def test_arithmetic_left_associative(self):
        expression = self.expression("10 - 3 - 2")
        self.assertEqual(expression.token.kind, T.MINUS)
        self.assertIsInstance(expression.left, A.Binary)
        self.assertEqual(expression.left.right.value, 3)

    def test_unary_minus_and_postfix(self):
        expression = self.expression("-f()[0] * 2")
        self.assertEqual(expression.token.kind, T.STAR)
        self.assertIsInstance(expression.left, A.Unary)
        self.assertIsInstance(expression.left.operand, A.Index)
        self.assertIsInstance(expression.left.operand.collection, A.Call)

    def test_boolean_precedence(self):
        expression = self.expression("not 1 < 2 and true or false")
        self.assertEqual(expression.token.kind, T.OR)
        self.assertEqual(expression.left.token.kind, T.AND)
        self.assertEqual(expression.left.left.token.kind, T.NOT)
        self.assertEqual(expression.left.left.operand.token.kind, T.LESS)

    def test_literals(self):
        self.assertIs(self.expression("true").value, True)
        self.assertIs(self.expression("false").value, False)
        self.assertIs(self.expression("nil").value, None)
        self.assertEqual(self.expression('"hi"').value, "hi")

    def test_declaration_and_assignment(self):
        statements = parse("let score = 1\nscore = score + 1")
        self.assertIsInstance(statements[0], A.VarDecl)
        self.assertEqual(statements[0].name.lexeme, "score")
        self.assertIsInstance(statements[1], A.Assign)
        self.assertIsInstance(statements[1].target, A.Variable)

    def test_index_assignment(self):
        statement = parse("xs[0][1] = 4")[0]
        self.assertIsInstance(statement, A.Assign)
        self.assertIsInstance(statement.target, A.Index)

    def test_invalid_assignment(self):
        with self.assertRaisesRegex(ParseError, "Assignment requires"):
            parse("1 + 2 = 4")

    def test_list_and_call(self):
        expression = self.expression('f([1, 2], "x")[0]')
        self.assertIsInstance(expression, A.Index)
        self.assertEqual(len(expression.collection.arguments), 2)
        self.assertIsInstance(expression.collection.arguments[0], A.ListExpr)

    def test_empty_list_and_call(self):
        self.assertEqual(self.expression("[]").elements, [])
        self.assertEqual(self.expression("f()").arguments, [])

    def test_if_elif_otherwise(self):
        source = "when false:\nprint(1)\nelif true:\nprint(2)\notherwise:\nprint(3)\nend"
        statement = parse(source)[0]
        self.assertIsInstance(statement, A.IfStmt)
        self.assertEqual(len(statement.branches), 2)
        self.assertEqual(len(statement.otherwise), 1)

    def test_nested_blocks_and_loop_control(self):
        source = "while true:\nwhen true:\nbreak\nend\ncontinue\nend\n"
        statement = parse(source)[0]
        self.assertIsInstance(statement, A.WhileStmt)
        self.assertIsInstance(statement.body[0].branches[0][1][0], A.BreakStmt)
        self.assertIsInstance(statement.body[1], A.ContinueStmt)

    def test_for(self):
        statement = parse("for item in range(3):\nprint(item)\nend")[0]
        self.assertIsInstance(statement, A.ForStmt)
        self.assertEqual(statement.name.lexeme, "item")

    def test_function_with_and_without_return_value(self):
        statements = parse("fn add(a, b):\nreturn a + b\nend\nfn empty():\nreturn\nend")
        self.assertEqual([p.lexeme for p in statements[0].parameters], ["a", "b"])
        self.assertIsInstance(statements[0].body[0], A.ReturnStmt)
        self.assertIsNone(statements[1].body[0].value)

    def test_duplicate_parameters_rejected(self):
        with self.assertRaisesRegex(ParseError, "Duplicate parameter"):
            parse("fn f(a, a):\nend")

    def test_return_outside_function(self):
        with self.assertRaisesRegex(ParseError, "inside a function"):
            parse("return 1")

    def test_loop_control_outside_loop(self):
        for source in ("break", "continue", "when true:\nbreak\nend"):
            with self.subTest(source=source), self.assertRaisesRegex(ParseError, "inside a loop"):
                parse(source)

    def test_function_cannot_break_enclosing_loop(self):
        source = "while true:\nfn f():\nbreak\nend\nend"
        with self.assertRaisesRegex(ParseError, "inside a loop"):
            parse(source)

    def test_function_can_have_own_loop(self):
        source = "fn f():\nwhile true:\nbreak\nend\nreturn\nend"
        self.assertIsInstance(parse(source)[0], A.FunctionStmt)

    def test_eof_in_block_is_incomplete(self):
        for source in ("when true:\n", "while true:\nprint(1)\n", "fn f():\nreturn 1\n"):
            with self.subTest(source=source), self.assertRaises(IncompleteInput):
                parse(source)

    def test_eof_in_expression_is_incomplete(self):
        for source in ("let x =", "print(", "[1,", "when true:"):
            with self.subTest(source=source), self.assertRaises(IncompleteInput):
                parse(source)

    def test_unclosed_expression_at_newline_is_error(self):
        with self.assertRaises(ParseError) as caught:
            parse("print(\n")
        self.assertNotIsInstance(caught.exception, IncompleteInput)

    def test_no_chained_comparisons(self):
        with self.assertRaisesRegex(ParseError, "Chained comparisons"):
            parse("1 < 2 < 3")

    def test_no_trailing_commas(self):
        for source in ("[1,]", "f(1,)", "fn f(a,):\nend"):
            with self.subTest(source=source), self.assertRaises(ParseError):
                parse(source)

    def test_one_statement_per_line(self):
        with self.assertRaisesRegex(ParseError, "newline"):
            parse("let x = 1 let y = 2")
        with self.assertRaisesRegex(ParseError, "newline"):
            parse("when true: print(1)\nend")

    def test_blank_lines_comments_and_empty_blocks(self):
        statements = parse("\n# hi\nwhen true:\n# empty\nend\n\n")
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0].branches[0][1], [])

    def test_error_location(self):
        with self.assertRaises(ParseError) as caught:
            parse("let x = 1\nlet = 2\n")
        self.assertEqual((caught.exception.line, caught.exception.column), (2, 5))

    def test_deep_expressions_are_language_errors(self):
        for source in ("(" * 2000 + "1" + ")" * 2000, "-" * 2000 + "1"):
            with self.subTest(prefix=source[:10]), self.assertRaisesRegex(ParseError, "nesting limit"):
                parse(source)


if __name__ == "__main__":
    unittest.main()
