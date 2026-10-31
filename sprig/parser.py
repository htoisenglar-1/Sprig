"""Recursive descent parsing; each precedence level has its own method."""

from . import ast_nodes as A
from .errors import IncompleteInput, ParseError
from .tokens import Token, TokenType as T


COMPARISONS = (T.EQUAL_EQUAL, T.BANG_EQUAL, T.LESS, T.LESS_EQUAL,
               T.GREATER, T.GREATER_EQUAL)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0
        self.function_depth = 0
        self.loop_depth = 0

    def parse(self) -> list[A.Stmt]:
        try:
            statements = []
            self._skip_newlines()
            while not self._check(T.EOF):
                statements.append(self._statement())
                self._skip_newlines()
            return statements
        except RecursionError:
            token = self._peek()
            raise ParseError(
                "Syntax nesting limit exceeded; simplify the expression or block nesting.",
                token.line, token.column,
            ) from None

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _check(self, kind: T) -> bool:
        return self._peek().kind == kind

    def _advance(self) -> Token:
        token = self._peek()
        if token.kind != T.EOF:
            self.current += 1
        return token

    def _match(self, *kinds: T) -> bool:
        if self._peek().kind not in kinds:
            return False
        self._advance()
        return True

    def _error(self, token: Token, message: str):
        error = IncompleteInput if token.kind == T.EOF else ParseError
        return error(message, token.line, token.column)

    def _consume(self, kind: T, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        raise self._error(self._peek(), message)

    def _skip_newlines(self) -> None:
        while self._match(T.NEWLINE):
            pass

    def _statement_end(self) -> None:
        if self._match(T.NEWLINE) or self._check(T.EOF):
            return
        raise self._error(self._peek(), "Expected a newline after the statement.")

    def _header_end(self) -> None:
        self._consume(T.COLON, "Expected ':' before the block.")
        self._consume(T.NEWLINE, "Expected a newline after ':'.")

    def _body(self, *terminators: T) -> list[A.Stmt]:
        statements = []
        self._skip_newlines()
        while self._peek().kind not in terminators:
            if self._check(T.EOF):
                raise self._error(self._peek(), "Expected 'end' to close the block.")
            statements.append(self._statement())
            self._skip_newlines()
        return statements

    def _close_block(self) -> None:
        self._consume(T.END, "Expected 'end' to close the block.")
        self._statement_end()

    def _statement(self) -> A.Stmt:
        if self._match(T.LET):
            token = self._previous()
            name = self._consume(T.IDENTIFIER, "Expected a variable name after 'let'.")
            self._consume(T.EQUAL, "Expected '=' after the variable name.")
            value = self._expression()
            self._statement_end()
            return A.VarDecl(token, name, value)
        if self._match(T.WHEN):
            return self._if_statement(self._previous())
        if self._match(T.WHILE):
            return self._while_statement(self._previous())
        if self._match(T.FOR):
            return self._for_statement(self._previous())
        if self._match(T.FN):
            return self._function_statement(self._previous())
        if self._match(T.RETURN):
            token = self._previous()
            if not self.function_depth:
                raise self._error(token, "'return' is only allowed inside a function.")
            value = None if self._peek().kind in (T.NEWLINE, T.EOF) else self._expression()
            self._statement_end()
            return A.ReturnStmt(token, value)
        if self._match(T.BREAK, T.CONTINUE):
            token = self._previous()
            if not self.loop_depth:
                raise self._error(token, f"'{token.lexeme}' is only allowed inside a loop.")
            self._statement_end()
            return A.BreakStmt(token) if token.kind == T.BREAK else A.ContinueStmt(token)
        start = self._peek()
        expression = self._expression()
        if self._match(T.EQUAL):
            token = self._previous()
            if not isinstance(expression, (A.Variable, A.Index)):
                raise self._error(token, "Assignment requires a variable or list index on the left.")
            value = self._expression()
            self._statement_end()
            return A.Assign(token, expression, value)
        self._statement_end()
        return A.ExpressionStmt(start, expression)

    def _if_statement(self, token: Token) -> A.IfStmt:
        condition = self._expression()
        self._header_end()
        branches = [(condition, self._body(T.ELIF, T.OTHERWISE, T.END))]
        while self._match(T.ELIF):
            condition = self._expression()
            self._header_end()
            branches.append((condition, self._body(T.ELIF, T.OTHERWISE, T.END)))
        otherwise = []
        if self._match(T.OTHERWISE):
            self._header_end()
            otherwise = self._body(T.END)
        self._close_block()
        return A.IfStmt(token, branches, otherwise)

    def _while_statement(self, token: Token) -> A.WhileStmt:
        condition = self._expression()
        self._header_end()
        self.loop_depth += 1
        try:
            body = self._body(T.END)
        finally:
            self.loop_depth -= 1
        self._close_block()
        return A.WhileStmt(token, condition, body)

    def _for_statement(self, token: Token) -> A.ForStmt:
        name = self._consume(T.IDENTIFIER, "Expected a loop variable after 'for'.")
        self._consume(T.IN, "Expected 'in' after the loop variable.")
        iterable = self._expression()
        self._header_end()
        self.loop_depth += 1
        try:
            body = self._body(T.END)
        finally:
            self.loop_depth -= 1
        self._close_block()
        return A.ForStmt(token, name, iterable, body)

    def _function_statement(self, token: Token) -> A.FunctionStmt:
        name = self._consume(T.IDENTIFIER, "Expected a function name after 'fn'.")
        self._consume(T.LEFT_PAREN, "Expected '(' after the function name.")
        parameters = []
        names = set()
        if not self._check(T.RIGHT_PAREN):
            while True:
                parameter = self._consume(T.IDENTIFIER, "Expected a parameter name.")
                if parameter.lexeme in names:
                    raise self._error(parameter, f"Duplicate parameter '{parameter.lexeme}'.")
                names.add(parameter.lexeme)
                parameters.append(parameter)
                if not self._match(T.COMMA):
                    break
        self._consume(T.RIGHT_PAREN, "Expected ')' after parameters.")
        self._header_end()
        outer_loops = self.loop_depth
        self.loop_depth = 0
        self.function_depth += 1
        try:
            body = self._body(T.END)
        finally:
            self.function_depth -= 1
            self.loop_depth = outer_loops
        self._close_block()
        return A.FunctionStmt(token, name, parameters, body)

    def _expression(self) -> A.Expr:
        return self._or()

    def _or(self) -> A.Expr:
        expression = self._and()
        while self._match(T.OR):
            operator = self._previous()
            expression = A.Logical(operator, expression, self._and())
        return expression

    def _and(self) -> A.Expr:
        expression = self._not()
        while self._match(T.AND):
            operator = self._previous()
            expression = A.Logical(operator, expression, self._not())
        return expression

    def _not(self) -> A.Expr:
        if self._match(T.NOT):
            token = self._previous()
            return A.Unary(token, self._not())
        return self._comparison()

    def _comparison(self) -> A.Expr:
        expression = self._term()
        if self._match(*COMPARISONS):
            operator = self._previous()
            expression = A.Binary(operator, expression, self._term())
            if self._peek().kind in COMPARISONS:
                raise self._error(self._peek(), "Chained comparisons are not supported; combine comparisons with 'and'.")
        return expression

    def _term(self) -> A.Expr:
        expression = self._factor()
        while self._match(T.PLUS, T.MINUS):
            operator = self._previous()
            expression = A.Binary(operator, expression, self._factor())
        return expression

    def _factor(self) -> A.Expr:
        expression = self._unary()
        while self._match(T.STAR, T.SLASH, T.PERCENT):
            operator = self._previous()
            expression = A.Binary(operator, expression, self._unary())
        return expression

    def _unary(self) -> A.Expr:
        if self._match(T.MINUS):
            token = self._previous()
            return A.Unary(token, self._unary())
        return self._postfix()

    def _postfix(self) -> A.Expr:
        expression = self._primary()
        while True:
            if self._match(T.LEFT_PAREN):
                token = self._previous()
                arguments = []
                if not self._check(T.RIGHT_PAREN):
                    while True:
                        arguments.append(self._expression())
                        if not self._match(T.COMMA):
                            break
                self._consume(T.RIGHT_PAREN, "Expected ')' after arguments.")
                expression = A.Call(token, expression, arguments)
            elif self._match(T.LEFT_BRACKET):
                token = self._previous()
                index = self._expression()
                self._consume(T.RIGHT_BRACKET, "Expected ']' after the index.")
                expression = A.Index(token, expression, index)
            else:
                return expression

    def _primary(self) -> A.Expr:
        if self._match(T.NUMBER, T.STRING):
            token = self._previous()
            return A.Literal(token, token.literal)
        if self._match(T.TRUE, T.FALSE, T.NIL):
            token = self._previous()
            value = {T.TRUE: True, T.FALSE: False, T.NIL: None}[token.kind]
            return A.Literal(token, value)
        if self._match(T.IDENTIFIER):
            return A.Variable(self._previous())
        if self._match(T.LEFT_PAREN):
            expression = self._expression()
            self._consume(T.RIGHT_PAREN, "Expected ')' after the expression.")
            return expression
        if self._match(T.LEFT_BRACKET):
            token = self._previous()
            elements = []
            if not self._check(T.RIGHT_BRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(T.COMMA):
                        break
            self._consume(T.RIGHT_BRACKET, "Expected ']' after list elements.")
            return A.ListExpr(token, elements)
        raise self._error(self._peek(), "Expected an expression.")
