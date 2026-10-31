"""Independent tests: source text must become the correct token stream."""

import unittest

from sprig.errors import LexError
from sprig.lexer import Lexer
from sprig.tokens import KEYWORDS, TokenType as T


class LexerTests(unittest.TestCase):
    def scan(self, text):
        return Lexer(text).scan_tokens()

    def test_declaration_tokens_and_positions(self):
        tokens = self.scan("let hours = 2\n")
        self.assertEqual([token.kind for token in tokens],
                         [T.LET, T.IDENTIFIER, T.EQUAL, T.NUMBER, T.NEWLINE, T.EOF])
        self.assertEqual([token.column for token in tokens[:-1]], [1, 5, 11, 13, 14])
        self.assertEqual(tokens[3].literal, 2)
        self.assertEqual((tokens[-1].line, tokens[-1].column), (2, 1))

    def test_empty_source(self):
        tokens = self.scan("")
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].kind, T.EOF)

    def test_all_keywords(self):
        tokens = self.scan(" ".join(KEYWORDS))
        self.assertEqual([t.kind for t in tokens[:-1]], list(KEYWORDS.values()))

    def test_identifier_boundaries_and_case(self):
        tokens = self.scan("whenly Let _score score2")
        self.assertTrue(all(t.kind == T.IDENTIFIER for t in tokens[:-1]))

    def test_numbers_and_minus_are_separate(self):
        tokens = self.scan("-7 0 3.25")
        self.assertEqual([t.kind for t in tokens[:-1]], [T.MINUS, T.NUMBER, T.NUMBER, T.NUMBER])
        self.assertEqual([t.literal for t in tokens[1:-1]], [7, 0, 3.25])

    def test_string_escapes_and_comment_marker(self):
        source = r'"hello\n\t\r\"\\#"'
        self.assertEqual(self.scan(source)[0].literal, 'hello\n\t\r"\\#')

    def test_unicode_string_contents(self):
        self.assertEqual(self.scan('"Hello, 世界 🌱"')[0].literal, "Hello, 世界 🌱")

    def test_comment_does_not_consume_newline(self):
        tokens = self.scan("# hi\nlet x = 2 # rest\n")
        self.assertEqual(tokens[0].kind, T.NEWLINE)
        self.assertEqual(tokens[1].kind, T.LET)
        self.assertEqual(tokens[1].line, 2)
        self.assertEqual(tokens[-2].kind, T.NEWLINE)

    def test_crlf_and_bare_cr(self):
        tokens = self.scan("1\r\n2\r3")
        numbers = [t for t in tokens if t.kind == T.NUMBER]
        self.assertEqual([(t.line, t.column) for t in numbers], [(1, 1), (2, 1), (3, 1)])
        self.assertEqual(sum(t.kind == T.NEWLINE for t in tokens), 2)

    def test_punctuation_and_maximal_operator_matching(self):
        source = "+ - * / % = == != < <= > >= ( ) [ ] , :"
        expected = [T.PLUS, T.MINUS, T.STAR, T.SLASH, T.PERCENT, T.EQUAL,
                    T.EQUAL_EQUAL, T.BANG_EQUAL, T.LESS, T.LESS_EQUAL,
                    T.GREATER, T.GREATER_EQUAL, T.LEFT_PAREN, T.RIGHT_PAREN,
                    T.LEFT_BRACKET, T.RIGHT_BRACKET, T.COMMA, T.COLON]
        self.assertEqual([t.kind for t in self.scan(source)[:-1]], expected)

    def test_invalid_characters(self):
        for text in ("!", ";", "@", "'hello'", "é", "١"):
            with self.subTest(text=text), self.assertRaises(LexError):
                self.scan(text)

    def test_unterminated_strings(self):
        for text in ('"hello', '"hello\nworld"', '"hello\\', '"hello\\\nworld"'):
            with self.subTest(text=text), self.assertRaisesRegex(LexError, "Unterminated"):
                self.scan(text)

    def test_unknown_escape(self):
        with self.assertRaisesRegex(LexError, "Unknown string escape"):
            self.scan(r'"\q"')

    def test_invalid_decimal(self):
        for text in ("1.", "1.x", ".5"):
            with self.subTest(text=text), self.assertRaises(LexError):
                self.scan(text)

    def test_overflow_float_is_language_error(self):
        with self.assertRaisesRegex(LexError, "finite"):
            self.scan("9" * 400 + ".0")

    def test_error_locations_and_rendering(self):
        source = "let x = 1\n  @\n"
        with self.assertRaises(LexError) as caught:
            self.scan(source)
        error = caught.exception
        self.assertEqual((error.line, error.column), (2, 3))
        rendered = error.render(source, "bad.sprig")
        self.assertIn("bad.sprig:2:3: LexError:", rendered)
        self.assertIn("  @", rendered)
        self.assertEqual(rendered.splitlines()[-1], "      ^")


if __name__ == "__main__":
    unittest.main()
