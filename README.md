# Sprig 2

Sprig is a small language for learning how programs work. Version 2 keeps the interpreter in one Python file, with no extra packages. It reads Sprig source using its own lexer, parser, abstract syntax tree (AST), and interpreter.

## Run it

Use Python 3.10 or newer. From this folder:

```sh
python3 sprig.py examples/hello.sprig
```

You can also use `python3 -m sprig examples/hello.sprig`. No installation is needed.

```sh
python3 sprig.py                    # Interactive prompt
python3 sprig.py --version          # Sprig 2.0
python3 sprig.py --ast examples/hello.sprig
python3 -m unittest discover -s tests -v
```

At the prompt, enter a statement or expression. Close each block with `end`. Expressions display non-`nil` results. Use `:reset` to clear your variables and `:quit` to exit.

## Your first program

Save this as `first.sprig`, then run `python3 sprig.py first.sprig`:

```text
# A comment starts with #.
let name = "Ada"
let ready = true

when ready:
    print("Hello", name)
otherwise:
    print("Not ready")
end
```

Output:

```text
Hello Ada
```

A newline ends a statement. Indentation is for readability; `:` starts a block and `end` closes it. Each nested block needs its own `end`. Blank lines and empty blocks are allowed. Expressions and strings fit on one source line.

## Values and operators

| Value | Examples |
|---|---|
| Number | `12`, `3.5`, `-2` |
| String | `"hello"`, `"line\nbreak"` |
| Boolean | `true`, `false` |
| No value | `nil` |
| Function | A function created with `fn` |

Strings use double quotes. Supported escapes are `\"`, `\\`, `\n`, `\t`, and `\r`. Names use ASCII letters, digits, and underscores, starting with a letter or underscore. Keywords and names are case-sensitive.

Operators below are listed from weakest to strongest precedence:

| Operators | Example | Result |
|---|---|---|
| `or` | `false or true` | `true` |
| `and` | `true and false` | `false` |
| `not` | `not 2 == 3` | `true` |
| `==`, `!=`, `<`, `<=`, `>`, `>=` | `2 <= 3` | `true` |
| `+`, `-` | `8 - 2 + 1` | `7` |
| `*`, `/`, `%` | `7 % 3` | `1` |
| Unary `-` | `-3 * 2` | `-6` |
| Calls and parentheses | `double(2 + 3)` | `10`, if `double` doubles its argument |

Arithmetic uses numbers. `+` also joins two strings: `"a" + "b"` is `"ab"`. Division can produce a fraction: `5 / 2` is `2.5`. The remainder follows floor division: `-5 % 3` is `1`. Ordering comparisons require numbers.

Booleans are distinct from numbers: `true == 1` is `false`, and `true + 1` is an error. Numbers compare by value, so `1 == 1.0` is `true`. Other values of different types are unequal. Functions compare by identity.

Conditions, `and`, `or`, and `not` require booleans. `and` and `or` skip their right side when the result is already known:

```text
print(false and 1 / 0 == 0)  # false; division is skipped
print(true or missing)      # true; missing is never read
```

Use `1 < score and score < 10` instead of `1 < score < 10`. Parentheses can combine comparison results explicitly.

## Statements

Declare a variable with `let`, then assign to change it:

```text
let score = 4
score = score + 1
print(score)  # 5
```

A name must be declared before use. Declaring it twice in the same scope is an error. Assignment changes the nearest existing declaration. Assignment is a statement, so `print(score = 5)` is invalid.

Use `when` and an optional `otherwise` branch:

```text
when score >= 5:
    print("pass")
otherwise:
    print("try again")
end
```

Use `while` to repeat while a condition remains true:

```text
let count = 0
while count < 3:
    print(count)
    count = count + 1
end
```

Use `repeat` for a fixed count:

```text
repeat 3:
    print("Hello")
end
```

The count is evaluated once and must be a non-negative integer. `true` and `3.0` are not valid counts. Conditions and loops share their surrounding scope. Declare reusable variables before a loop, then assign inside it; repeatedly declaring the same name with `let` causes an error.

Define functions with `fn`, and return a value with `return`:

```text
fn factorial(n):
    when n <= 1:
        return 1
    end
    return n * factorial(n - 1)
end

print(factorial(5))  # 120
```

A function call creates a local scope. Parameters are local variables, and arguments are evaluated left to right. Calls need exactly the declared number of arguments. A bare `return`, or reaching the end, returns `nil`. `return` is only allowed inside a function.

Functions use lexical scope: they remember the environment where they were defined. They can be assigned, passed as arguments, returned, and nested. See `examples/scope.sprig` and `examples/closure.sprig`.

`print(...)` is the only built-in function. It prints any number of values separated by spaces, followed by a newline, and returns `nil`. Booleans display as `true` or `false`. Its name can be shadowed or reassigned like other names. An expression on its own is also a valid statement; in a file, use `print` to display it.

## Errors and examples

Sprig syntax and runtime errors include a source line number. Check the name, value, or syntax mentioned in the message:

| Error | What to check |
|---|---|
| Unexpected character or invalid string | Use the supported symbols and string escapes. |
| Expected token or expression | Check parentheses, `:`, newlines, and matching `end` keywords. |
| Undefined name | Declare the name with `let` or `fn` first. |
| Already declared | Use assignment to change an existing local variable. |
| Expected numbers or booleans | Give the operator or condition the right value type. |
| Division by zero | Check the divisor for `/` and `%`. |
| Expected argument count or function | Check the function name and its arguments. |
| Invalid repeat count | Use a non-negative integer. |

The `examples/` folder contains short programs and matching `.out` files. `examples/errors/` contains programs that should fail and `.err` files with expected message fragments. The test command checks these as well as language behavior.

## How it is built

The implementation is in `sprig.py`: source text becomes tokens, the parser builds tuple-based AST nodes, and the interpreter evaluates those nodes. A small environment object holds variables and links function scopes to their enclosing scopes. Sprig source is never passed to Python's `eval()` or `exec()`.

The complete syntax is in `grammar.ebnf`. This version uses dynamic value types, lexical function scope, and structured control flow. It keeps functions and recursion from the project reference's core requirements. Its three standard features are a second loop (`repeat`), first-class functions and closures, and an interactive prompt.

Version 2 focuses on a small implementation. Lists, indexing, `for`, `elif`, `break`, `continue`, classes, modules, and extra built-in functions are omitted. Existing Sprig programs using these features need to be simplified before running here.

This is an AI-assisted learning implementation. Review the source and grammar so you can explain how each part works. The course's separate report, slides, and presentation are outside this code update.
