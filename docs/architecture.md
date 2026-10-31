# How the interpreter fits together

A source file follows this path:

```text
source text -> lexer -> tokens -> parser -> AST -> interpreter -> values/output
                                                    |
                                               environments
```

The CLI and REPL sit around this pipeline. They provide source text, streams, arguments, and error display. They do not translate Sprig to Python source.

## Files and responsibilities

| File | Responsibility |
|---|---|
| `sprig/__init__.py` | Package identity/version |
| `sprig/tokens.py` | Token kinds and source-position token records |
| `sprig/lexer.py` | Scan characters, recognize literals/keywords/operators, track line/column |
| `sprig/ast_nodes.py` | Small dataclasses representing expressions and statements |
| `sprig/parser.py` | Recursive descent grammar, precedence, block structure, syntax validation |
| `sprig/errors.py` | Lexical, syntax, incomplete-input, and runtime error types and rendering |
| `sprig/values.py` | Callable/runtime value behavior, kind validation, display, equality |
| `sprig/environment.py` | Declarations, name lookup, assignment through parent environments |
| `sprig/interpreter.py` | Walk AST nodes, evaluate expressions, execute control flow and calls |
| `sprig/builtins.py` | Print/input, list helpers, conversions, range, and their validation |
| `sprig/runner.py` | Connect the pipeline and attach source context for diagnostics |
| `sprig/cli.py` | Parse options, read files, inspect tokens/AST, choose exit statuses |
| `sprig/repl.py` | Persistent interactive environment, unfinished-block buffer, commands |
| `sprig/__main__.py` | Launch the CLI using `python3 -m sprig` |
| `tests/` | Independent component tests and execution checks |
| `examples/` | Small complete Sprig programs |
| `docs/` | Tutorial, rules, rationale, and verification status |
| `pyproject.toml` | Python package metadata and optional console script |

Each AST node retains a source token. An operator error can therefore point to that operator instead of vaguely pointing to the beginning of a file. A runtime error also needs the source text and filename; the runner and function source context supply those.

## Three structures to distinguish

**Token:** a piece of source, such as a number or `+`, with its spelling and position.

**AST node:** a structured operation, such as addition with a left and right operand. The parser constructs it; the interpreter uses it.

**Runtime value:** the result of evaluating a node, such as the number `14`, a list, or a function object. A number token, a literal AST node, and the resulting number have related but different jobs.

## Environments and calls

The interpreter keeps a global environment whose parent contains protected built-ins. A function value stores a reference to its defining environment. On a call it creates a new child environment, declares the arguments under parameter names, then executes its body.

A lookup searches locally, then follows parent links. Assignment follows the same search and updates the nearest existing binding. Declaration stays local. These small rules produce lexical scope, recursion, shadowing, and closures without a complicated type hierarchy.

Blocks do not create new environments. This is deliberate, but it means a repeated declaration in a loop can fail on its second iteration. A `for` loop handles its iteration variable by creating or updating a local binding.

## Internal control signals

A return is not a failed user program. The interpreter uses private control signals to unwind from nested branches to the active function call. Break and continue similarly travel to their nearest loop. The parser rejects these statements in contexts where they have nowhere valid to go. A nested function starts a fresh loop context even when it is declared inside a loop.

## Runtime choices

Python supplies basic storage objects such as integers and lists. Sprig owns the rules applied to those objects. It explicitly separates booleans from numbers, rejects incompatible arithmetic, requires Boolean conditions, checks arity and indices, and provides its own value display.

This keeps early code manageable. A separate object hierarchy for every number and string would add machinery without teaching a new language behavior yet. Explicit runtime function objects and validation helpers are enough for version 0.1.

## Python embedding example

From the project folder:

```sh
python3 - <<'PY'
import io
from sprig.interpreter import Interpreter
from sprig.runner import run_source

output = io.StringIO()
interpreter = Interpreter(stdout=output)
run_source('let score = 6\nprint(score * 7)\n', interpreter, filename='<example>')
print(output.getvalue(), end='')
PY
```

Expected output is `42`. Reuse the interpreter object to retain globals across calls. This is also how tests can capture output without scraping a terminal. The step budget, when supplied, applies to each submission and counts executed statements, evaluated expressions, and `for` iterations.

## Extending a feature

1. Write a tiny example and decide its meaning.
2. Add tokens only if the source needs new pieces.
3. Add AST nodes and grammar only if the structure changes.
4. Implement execution and precise failures.
5. Test valid cases, invalid cases, and interactions with existing features.
6. Update examples and the reference.

A new ordinary built-in usually needs only runtime validation, registration, tests, and documentation. A new block statement often touches parser and interpreter as well. Avoid changing every module just because a feature is new.
