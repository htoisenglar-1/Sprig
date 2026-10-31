# Building and learning Sprig, one stage at a time

Read one stage, run its commands, and try its exercise before moving on. The complete implementation is in the named project files; the short snippets here highlight the ideas rather than duplicate every module. Expected outputs below describe the language contract. The project's actual verification record is in `roadmap.md`.

Commands assume macOS Terminal and Python 3.10 or newer. To start a completely empty project folder, use `mkdir -p ~/Desktop/sprig/{sprig,tests,examples,docs}`. In this supplied project the files already exist: do not replace them with empty files. Enter it with:

```sh
cd ~/Desktop/sprig
python3 --version
```

An optional isolated Python environment can be created with:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

The interpreter and tests use the standard library. You can run them directly from the project folder without installing anything. The optional `sprig` shell command is explained in the README.

## Stage 1 — Design a language before implementing it

**Concept.** Syntax describes legal spelling; semantics describes meaning. A language specification is an agreement between a programmer and the interpreter.

Sprig is our working name, with `.sprig` source files. Its purpose is readable programs and an implementation we can understand. Python implements Sprig; Python does not interpret Sprig's source syntax for us.

```text
let hours = 2
let minutes = hours * 60
print(minutes)
```

Expected output: `120`.

**Implementation.** Read `language-design.md` for the choices and `language-reference.md` for the full rules. `examples/hello.sprig` is the original design example. Variables require `let` for declaration, blocks close with `end`, and Boolean conditions use `when`.

**Run and check.** With the completed interpreter:

```sh
python3 -m sprig examples/hello.sprig
```

Expected output:

```text
Hello, Crystal
14
Goal reached!
```

**Debugging.** `=` means assignment; `==` means comparison. A design example becomes an executable program only when the corresponding interpreter feature exists. A working interpreter is evidence about the implementation, not a replacement for precise rules.

**Exercise.** Write a three-line hours-to-minutes program and predict its output before running it.

## Stage 2 — Turn characters into tokens

**Concept.** A lexer groups individual characters into meaningful pieces called tokens. `let hours = 2` contains a keyword, a name, an operator, and a number. A token also remembers where it came from so errors can point to the correct place.

Conceptually:

```text
LET  IDENTIFIER("hours")  EQUAL  NUMBER(2)  NEWLINE  EOF
```

`EOF` marks the end of the input. The minus in `-2` is its own token; the parser later decides that it negates a number. The lexer reads a double-quoted string as one value, so `#` inside it is ordinary text.

**Implementation.** Read `sprig/tokens.py`, then `sprig/lexer.py`. `TokenType` names the possible pieces. `Token` stores kind, source spelling, decoded literal, line, and column. The lexer advances through the source and emits tokens. `sprig/errors.py` defines errors with source positions.

**Run and test.** Inspect the tiny fragment directly:

```sh
python3 - <<'PY'
from sprig.lexer import Lexer
for token in Lexer('let hours = 2\n').scan_tokens():
    print(token.kind.name, repr(token.lexeme), repr(token.literal))
PY
python3 -m unittest discover -s tests -p 'test_lexer.py' -v
python3 -m sprig --tokens examples/arithmetic.sprig
```

Check that the fragment produces the six token kinds listed above, and that the number token's literal is `2`. Test output should finish with `OK`; a failing test is a reason to investigate, not to skip ahead.

**Debugging.** Unknown symbols, unclosed strings, and unsupported escapes belong to the lexer. Check its current character, line, and column. A missing `end` is not a lexer problem: `end` is simply another word at this layer.

**Exercise.** Predict the tokens in `print("a#b", 3.5)` and confirm that `#b` does not become a comment.

## Stage 3 — Turn tokens into a syntax tree

**Concept.** A parser checks grammar and turns a flat token stream into an abstract syntax tree, or AST. An AST records meaning-bearing structure, omitting details such as redundant parentheses.

For `2 + 3 * 4`, the shape is:

```text
      +
     / \
    2   *
       / \
      3   4
```

Multiplication is a child of addition, so it happens first. Parentheses change the shape. This is operator precedence.

**Implementation.** Read `sprig/ast_nodes.py` and `sprig/parser.py`. Dataclasses hold the tree nodes. The recursive descent parser uses a small method for each grammar level. A declaration creates a `VarDecl` node; addition creates a `Binary` node; a variable reference creates a `Variable` node. The parser does not calculate the result.

**Run and test.**

```sh
python3 -m unittest discover -s tests -p 'test_parser.py' -v
python3 -m sprig --ast examples/arithmetic.sprig
```

Inspect the tree for the first calculation in `arithmetic.sprig`: multiplication should appear beneath addition. Automated tests should finish with `OK`. Try invalid code `let = 2` in a scratch `.sprig` file: it must be rejected before execution.

**Debugging.** If arithmetic groups incorrectly, inspect the AST before changing the evaluator. Unexpected-token errors usually mean a missing name, expression, delimiter, or newline. A syntax error at EOF can mean the parser needs more input; the REPL uses that distinction to collect blocks.

**Exercise.** Draw trees for `10 - 3 - 2` and `10 - (3 - 2)`. Predict `5` and `9`.

## Stage 4 — Evaluate the tree with an environment

**Concept.** An interpreter walks AST nodes and performs the operation each node describes. An environment is a mapping from names to values: after `let score = 14`, it remembers that `score` refers to `14`.

```text
let score = 8 + 2 * 3
score = score + 1
print(score)
```

Expected output: `15`.

**Implementation.** Read `sprig/environment.py`, `sprig/values.py`, `sprig/interpreter.py`, and `sprig/builtins.py`. A literal evaluates to its value. A variable asks the environment for its binding. A binary expression evaluates operands and validates their kinds. A declaration stores a new binding; an assignment updates an existing one. A call evaluates its callee and arguments, then invokes the Sprig callable.

The implementation uses Python objects internally, but Sprig applies its own rules. In particular, Python's `bool` is an integer subclass; Sprig explicitly prevents booleans from participating in arithmetic.

**Run and test.**

```sh
python3 -m sprig examples/arithmetic.sprig
python3 -m unittest discover -s tests -p 'test_runtime.py' -v
```

The example's intended output is:

```text
14
20
2.5
true
hello Sprig
```

**Debugging.** `print(missing)` should report an undefined name. `print("score=" + 3)` should report invalid operand kinds; use `print("score=", 3)` or explicit `str(3)`. Do not silently convert invalid values to make an example pass.

**Exercise.** Store a rectangle's width and height, calculate its area, and print the result. Then deliberately misspell one variable and read the error location.

## Stage 5 — Add branches and repeated execution

**Concept.** Control flow chooses which statements execute and how many times. A `when` runs one branch. A `while` repeats while its Boolean condition stays true. A `for` visits elements of a list or string.

```text
let count = 0
while count < 3:
    print(count)
    count = count + 1
end
```

Expected output: `0`, `1`, `2`, on separate lines.

**Implementation.** Follow `IfStmt`, `WhileStmt`, and `ForStmt` from parser to interpreter. The parser builds a body list; the interpreter executes that list only when appropriate. `break` and `continue` use private control signals so they can leave nested statement execution cleanly. Blocks share their surrounding environment.

**Run and test.**

```sh
python3 -m sprig --max-steps 10000 examples/loops.sprig
python3 -m unittest discover -s tests -p 'test_runtime.py' -v
```

Expected example output:

```text
0
1
2
1
3
three
```

**Debugging.** A missing update in a `while` loop may run forever; use `--max-steps` while experimenting. Conditions such as `when 1:` are invalid because Sprig requires a boolean. Repeatedly declaring the same name inside a loop causes a redeclaration error. Declare it before the loop and update it inside. Every nested block needs its own `end`.

**Exercise.** Sum the integers from 1 through 10 using `for` and `range`. The result should be `55`. Then implement the same task with `while`.

## Stage 6 — Functions, local scope, closures, and lists

**Concept.** A function packages a reusable computation. Parameters become local bindings for one call. A closure is a function that remembers the environment where it was defined, even after the outer function returns. Lists hold a changeable sequence of values.

```text
fn double(value):
    return value * 2
end
let numbers = [2, 4]
append(numbers, double(3))
print(numbers)
```

Expected output: `[2, 4, 6]`.

**Implementation.** Follow `FunctionStmt`, `Call`, `ReturnStmt`, `ListExpr`, and `Index`. The runtime function value stores its parameter names, body, and defining environment. Calling it creates a child environment. A return uses a private signal. Lists are shared mutable values: passing one to a function does not copy it.

Assignment walks outward to the nearest existing binding. `let` always creates locally, so it can shadow an outer name. This makes the counter example possible without a separate `global` keyword. Recursion works because the function name is bound in the environment that the function remembers.

**Run and test.**

```sh
python3 -m sprig examples/functions.sprig
python3 -m sprig examples/closures.sprig
python3 -m sprig examples/lists.sprig
python3 -m unittest discover -s tests -p 'test_runtime.py' -v
```

Intended outputs, in order:

```text
120
nil
```

```text
1
2
1
```

```text
[2, 4, 6]
6
[2, 4]
2
true
```

**Debugging.** Check function arity, the environment where a name was declared, and whether a list is shared. `return` outside a function and `break` outside a loop are syntax errors. Deep recursion eventually reaches the host recursion limit; prefer loops for very deep repetition.

**Exercise.** Write `sum_items(items)` that returns the sum of a numeric list. Then write a closure that starts its counter at a supplied parameter.

## Stage 7 — Make runtime rules and errors deliberate

**Concept.** Invalid user programs should produce useful language errors, not unexpected Python tracebacks. A runtime layer validates operands, argument counts, indices, input, conversions, and resource limits.

```text
let numerator = 10
print(numerator / 0)
```

Expected behavior: a Sprig runtime error pointing to the division on line 2. Exact message wording may evolve; filename, line, column, source, and caret should remain useful.

**Implementation.** Read `sprig/errors.py`, validation helpers in `values.py`, and built-in validation in `builtins.py`. `input` reads through an injected stream so tests can supply answers without waiting for a keyboard. `runner.py` connects lexing, parsing, execution, and source context. Functions remember definition context so a later REPL call can report an error in the correct earlier source.

**Run and test.**

```sh
printf 'Ada\n' | python3 -m sprig examples/input.sprig
python3 -m unittest discover -s tests -v
```

Expected input example output: `Your name: Hello, Ada` followed by a newline. The prompt and answer are adjacent in piped output because the input itself is not echoed.

Also try `print([1][5])`, `number("oops")`, and `when 1:` in separate scratch files. Each should give a readable error. Errors preserve successful effects that already happened; there is no automatic rollback.

**Debugging.** Distinguish lexical errors (bad characters/strings), syntax errors (bad structure), and runtime errors (valid syntax with invalid operations). Follow the caret first. A step budget reduces accidental endless evaluation, but it does not make the interpreter a sandbox or impose a memory/time limit.

**Exercise.** Make three intentionally broken programs, one for each error category. Explain which component should reject each one and why.

## Stage 8 — Provide a file runner and a REPL

**Concept.** A command-line interface reads files and options. A REPL is a read–evaluate–print loop; it retains the environment between submissions. In this first Sprig REPL, use `print` explicitly to display values.

**Implementation.** Read `sprig/cli.py`, `sprig/repl.py`, and `sprig/__main__.py`. The CLI handles UTF-8 files, argument lists, inspection modes, error display, and exit status. `__main__.py` makes `python3 -m sprig` work. The REPL keeps a buffer while a block is incomplete and one interpreter for successful submissions. An optional step budget resets for each submission and counts evaluated expressions, executed statements, and `for` iterations.

**Run and test.**

```sh
python3 -m sprig --help
python3 -m sprig --version
python3 -m sprig examples/arguments.sprig Ada 3
python3 -m sprig
```

The argument example should print:

```text
Ada
Ada
Ada
```

In the REPL, enter:

```text
let total = 2
print(total + 3)
fn twice(value):
    return value * 2
end
print(twice(total))
:quit
```

Expected program output: `5` and `4`, in addition to the banner and prompts. Try `:reset` in a new session, then `print(total)`: the variable should be gone.

**Debugging.** Run from the project folder so Python finds the `sprig` package, or use the installed console command in its virtual environment. Save Sprig code with the `.sprig` extension. Put interpreter options before the filename; words after it are script arguments. Ctrl-C cancels an unfinished REPL entry; EOF exits. A runtime failure does not undo earlier bindings or list changes.

**Exercise.** Write a program that reads its first command-line argument as a number and prints its square. Show a helpful message when the argument is missing.

## Stage 9 — Test, document, and prepare for other readers

**Concept.** Tests turn expectations into repeatable checks. Independent lexer and parser tests isolate failures; runtime tests check language semantics; CLI tests check the actual user entry point. Documentation explains both use and implementation.

**Implementation.** Read the `tests/` folder and `architecture.md`. Tests use Python's `unittest`, in-memory streams, and subprocesses where appropriate. `pyproject.toml` describes the optional installable package and console entry point. Keep the interpreter free of unnecessary runtime dependencies.

**Run and check.**

```sh
python3 -m unittest discover -s tests -v
python3 -m sprig examples/hello.sprig
python3 -m sprig --tokens examples/arithmetic.sprig
python3 -m sprig --ast examples/arithmetic.sprig
```

A successful test run ends with `OK`. The exact count and environment used for the completed project are recorded in `roadmap.md` after verification. Do not claim a feature works solely because its code looks plausible.

For future GitHub publication, review `.gitignore`, README, examples, and package metadata first. A local repository can be started with `git init` and `git add .` when you are ready. Publishing requires choosing an account, repository, and license; this project does not silently choose or publish them for you. Do not commit `.venv`, caches, or secrets. No open-source license is implied by these files.

**Debugging.** Run the smallest failing test first. Reduce a bug to a tiny Sprig program. Decide whether the wrong result starts in tokens, tree shape, environment lookup, or evaluation. Add a regression test for the behavior, then fix the responsible module.

**Exercise.** Add a test for an edge case such as an empty list, Unicode string indexing, or a closure modifying an enclosing value. State the expected behavior before reading the implementation.

## Stage 10 — Explore only after the core is reliable

Modules, dictionaries, classes, a standard library, package management, and debugging are later language-design projects. Start with examples and rules, then extend tokens, AST, parser, runtime, tests, and reference only where needed.

A tree-walking interpreter is easy to inspect. A bytecode virtual machine replaces repeated AST walking with a small instruction stream; it adds a compiler, stack rules, instruction definitions, and debugging work. Measure a meaningful bottleneck before deciding whether those costs help Sprig.

**Study exercise.** Design a dictionary literal and three example operations on paper. Decide equality, mutation, allowed key kinds, and error behavior before writing code. Stage 10 features are intentionally not implemented in version 0.1.
