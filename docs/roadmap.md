# Development roadmap and verification

## Milestones

| Stage | Deliverable | Status |
|---|---|---|
| 1 | Name, syntax, semantics, tiny source program | Complete; example executed |
| 2 | Tokens, lexer, locations, independent lexer tests | Complete; verified |
| 3 | AST, recursive descent parser, precedence, parser tests | Complete; verified |
| 4 | Evaluator, environments, arithmetic, printing | Complete; verified |
| 5 | Conditions, while/for, break/continue, scope rules | Complete; verified |
| 6 | Functions, lexical closures, returns, lists | Complete; verified |
| 7 | Built-ins, runtime validation, source errors | Complete; verified |
| 8 | File runner, command arguments, REPL, optional installation | Complete; verified |
| 9 | Automated tests, examples, reference, beginner tutorial | Complete; tests and examples verified locally |
| 10 | Modules, dictionaries, classes, packages, debugger, bytecode VM | Future study; intentionally deferred |

The initial Stage 1 files were saved before implementation. The later work builds the runnable core and documents each layer, with tests used to verify behavior. Stages 1–9 now provide the runnable version 0.1. Stage 10 remains a future study plan.

## Verification record

Verified on October 27, 2026, on macOS using Python 3.14.7.

- The full test suite passed in the Desktop project: **110 tests**, including all eight supplied examples as output-checked subtests. The same suite also passed in the build workspace.
- Each of the eight examples was executed separately through the CLI. Input was supplied as `Ada`, and the arguments example received `Ada 3`; outputs matched the tutorial.
- CLI subprocess tests verified file arguments, token/AST inspection without execution, readable errors, UTF-8 failures, step budgets, and interrupted-file exit status 130.
- REPL tests verified persistent variables, multiline functions, recovery after errors, reset/help, EOF during an incomplete block, cancellation with Ctrl-C, and error locations in earlier function definitions.
- Edge tests covered huge numeric values, deep syntax and runtime nesting, cyclic lists, and a list shrinking during indexed assignment. An independent 5,000-case malformed-input review found no leaked host exceptions; it supplements rather than replaces the committed regression suite.
- A wheel was built and installed into `~/Desktop/sprig/.venv`. Its console command ran the hello example successfully from outside the source folder. Import inspection confirmed the installed copy was used.
- Source was checked for calls to Python eval, exec, and compile; none were found in the interpreter package.

The source runner and tests need no third-party runtime dependencies. Package building uses setuptools, fetched into isolated build tooling during installation verification. No global Python package was installed or upgraded.

Only the Python/macOS environment above was executed here. Python 3.10+ is the declared target, not a claim that every supported interpreter or operating system has been tested. Host recursion/digit limits, finite floats, and the 100,000-element range cap remain documented limits.

Standard check commands from the Desktop project folder:

```sh
cd ~/Desktop/sprig
python3 --version
python3 -m unittest discover -s tests -v
python3 -m sprig examples/hello.sprig
python3 -m sprig examples/arithmetic.sprig
python3 -m sprig examples/loops.sprig
python3 -m sprig examples/functions.sprig
python3 -m sprig examples/closures.sprig
python3 -m sprig examples/lists.sprig
printf 'Ada\n' | python3 -m sprig examples/input.sprig
python3 -m sprig examples/arguments.sprig Ada 3
python3 -m sprig --tokens examples/arithmetic.sprig
python3 -m sprig --ast examples/arithmetic.sprig
```

REPL checks should include persistent variables, a multiline function, recovery after a syntax/runtime error, reset, EOF with an incomplete block, and a runtime error in a function defined in a previous submission. File-runner checks should include missing files, invalid UTF-8, unsupported file extension, nonzero error exit, and a step-budget failure.

## Publication remains separate

Package metadata enables local installation; it is not a package-index release. No GitHub repository, remote push, package publication, license choice, or claim to the working name is implied. Choose those deliberately before inviting other people to install or contribute.
