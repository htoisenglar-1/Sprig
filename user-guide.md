# Sprig 2 User Guide

Sprig is a small programming language for learning how programs run. You write a Sprig program in a text file, then run it with the Sprig interpreter. This guide is for someone using Sprig for the first time.

## 1. Install and run Sprig

Sprig needs Python 3.10 or newer. It has no third-party dependencies.

From the project folder, run a file with:

```sh
python3 sprig.py examples/hello.sprig
```

You can also run the module form:

```sh
python3 -m sprig examples/hello.sprig
```

Useful commands:

```sh
python3 sprig.py --version                 # show the Sprig version
python3 sprig.py --ast examples/hello.sprig # show the abstract syntax tree
python3 -m unittest discover -s tests -v   # run the project checks
python3 sprig.py                           # open the interactive prompt
```

Sprig source files use the `.sprig` extension. A line normally contains one statement. Spaces and indentation make code easier to read, but indentation does not decide where a block ends. A colon starts a block and `end` closes it.

## 2. Write your first program

Create a file named `first.sprig` with this content:

```sprig
# A comment starts with #.
let name = "Ada"
let ready = true

when ready:
    print("Hello", name)
otherwise:
    print("Not ready")
end
```

Run it:

```sh
python3 sprig.py first.sprig
```

Output:

```text
Hello Ada
```

The program does four things:

1. `let name = "Ada"` declares a variable named `name`.
2. `let ready = true` declares a boolean variable.
3. `when ready:` chooses the first branch because `ready` is `true`.
4. `print("Hello", name)` writes two values separated by a space.

Comments begin with `#` and continue to the end of the line. Blank lines are allowed. Strings use double quotes. A block must have its own `end`, including a block nested inside another block.

## 3. Values and names

Sprig has five kinds of values:

| Value | Examples | Notes |
|---|---|---|
| Number | `12`, `3.5`, `-2` | Integers and finite decimal numbers |
| String | `"hello"` | Double-quoted text |
| Boolean | `true`, `false` | Used by conditions and logical operators |
| Nil | `nil` | Means “no value” |
| Function | `fn` declarations | Functions can be stored, passed, and returned |

Names can contain letters, digits, and underscores, but must start with a letter or underscore. Names are case-sensitive: `score`, `Score`, and `SCORE` are different names. Reserved words such as `let`, `when`, and `true` cannot be used as names.

Strings support these escapes:

| Escape | Meaning |
|---|---|
| `\"` | A double quote |
| `\\` | A backslash |
| `\n` | A newline inside the string |
| `\t` | A tab |
| `\r` | A carriage return |

Example:

```sprig
print("first line\nsecond line")
```

Output:

```text
first line
second line
```

## 4. Statements

### Declaration with `let`

`let` creates a new variable in the current scope.

```sprig
let score = 10
print(score)
```

Output:

```text
10
```

The initializer is evaluated before the variable is created. You cannot declare the same name twice in one scope.

### Assignment

Assignment changes a variable that already exists.

```sprig
let score = 10
score = score + 5
print(score)
```

Output:

```text
15
```

Assignment cannot introduce a new name. Use `let` first. Assignment updates the nearest existing declaration, which matters when functions and nested scopes are involved.

### Conditional with `when`

`when` runs its body when a boolean condition is true.

```sprig
let temperature = 30
when temperature > 25:
    print("warm")
end
```

Output:

```text
warm
```

The condition must be `true` or `false`. Sprig does not treat numbers or strings as automatically true or false.

### Alternative branch with `otherwise`

Add `otherwise` when there is a second path.

```sprig
let score = 62
when score >= 75:
    print("Passed")
otherwise:
    print("Try again")
end
```

Output:

```text
Try again
```

Only one branch runs. The `otherwise` branch is optional.

### Conditional loop with `while`

`while` repeats its body while its condition remains true.

```sprig
let count = 1
while count <= 3:
    print(count)
    count = count + 1
end
```

Output:

```text
1
2
3
```

The condition is checked before every iteration. Make sure something in the body changes the condition, or the loop may never finish.

### Counted loop with `repeat`

`repeat` runs its body a fixed number of times.

```sprig
repeat 3:
    print("Sprig")
end
```

Output:

```text
Sprig
Sprig
Sprig
```

The count is evaluated once and must be a non-negative integer. `3.0`, `true`, and `-1` are invalid repeat counts.

### Function declaration with `fn`

`fn` creates a named function. Parameters are local to the function call.

```sprig
fn add(left, right):
    return left + right
end

print(add(2, 3))
```

Output:

```text
5
```

Functions need exactly the number of arguments declared in their parameter list. A function can call itself recursively:

```sprig
fn factorial(n):
    when n <= 1:
        return 1
    end
    return n * factorial(n - 1)
end

print(factorial(5))
```

Output:

```text
120
```

Functions use lexical scope: they remember the environment where they were defined. Functions can be assigned to variables, passed to other functions, returned from functions, and nested inside functions.

### Return with `return`

`return` sends a value back to the caller and ends the current function.

```sprig
fn label(score):
    when score >= 75:
        return "pass"
    end
    return "try again"
end

print(label(80))
```

Output:

```text
pass
```

A bare `return` returns `nil`:

```sprig
fn stop():
    return
end

print(stop())
```

Output:

```text
nil
```

`return` is only legal inside a function.

### Expression statement

An expression can appear by itself as a statement.

```sprig
2 + 3
```

In a file, this evaluates the expression but does not print it. Use `print` when you want visible output. In the interactive prompt, a non-`nil` result is displayed automatically.

### Output with `print`

`print` is Sprig’s only built-in function. It accepts any number of values, separates them with spaces, prints a newline, and returns `nil`.

```sprig
print("Score:", 85, true, nil)
```

Output:

```text
Score: 85 true nil
```

The name `print` is an ordinary name, so a program can shadow or reassign it. Avoid doing that until you understand functions and environments.

## 5. Operators

The examples below show every Sprig operator. Operators are listed from weaker binding to stronger binding. Parentheses can always be used to make the grouping clear.

### Logical operators

`or` is true when either boolean is true.

```sprig
print(false or true)
```

Output: `true`

`and` is true only when both booleans are true.

```sprig
print(true and false)
```

Output: `false`

`not` reverses a boolean.

```sprig
print(not false)
```

Output: `true`

`and` and `or` short-circuit. The right side is skipped when the left side already determines the answer:

```sprig
print(false and missing)  # false; missing is never looked up
print(true or 1 / 0 == 0) # true; division is never attempted
```

Logical operators require booleans. Sprig does not use truthiness.

### Equality and ordering

`==` tests equality.

```sprig
print(1 == 1.0)
```

Output: `true`

`!=` tests inequality.

```sprig
print(2 != 3)
```

Output: `true`

`<` tests whether the left number is smaller.

```sprig
print(2 < 3)
```

Output: `true`

`<=` tests whether the left number is smaller or equal.

```sprig
print(3 <= 3)
```

Output: `true`

`>` tests whether the left number is larger.

```sprig
print(4 > 3)
```

Output: `true`

`>=` tests whether the left number is larger or equal.

```sprig
print(4 >= 4)
```

Output: `true`

Ordering operators require two numbers. Comparisons do not chain. Write `1 < score and score < 10`, not `1 < score < 10`.

Booleans are separate from numbers:

```sprig
print(true == 1)
```

Output: `false`

### Arithmetic

`+` adds numbers or joins two strings.

```sprig
print(2 + 3)
print("Spr" + "ig")
```

Output:

```text
5
Sprig
```

`-` subtracts the right number from the left.

```sprig
print(8 - 3)
```

Output: `5`

`*` multiplies numbers.

```sprig
print(4 * 3)
```

Output: `12`

`/` divides numbers and can produce a fraction.

```sprig
print(5 / 2)
```

Output: `2.5`

`%` returns the remainder.

```sprig
print(7 % 3)
```

Output: `1`

Unary `-` makes a number negative or changes its sign.

```sprig
print(-3)
```

Output: `-3`

Arithmetic requires numbers, except for string-plus-string. Mixed values such as `"5" + 1` are errors. Division and remainder by zero are errors.

### Calls and grouping

Parentheses group an expression:

```sprig
print((2 + 3) * 4)
```

Output: `20`

Parentheses also call a function:

```sprig
fn double(n):
    return n * 2
end

print(double(4))
```

Output: `8`

Calls bind tightly, so `double(2 + 3)` passes `5` to `double`.

## 6. Scope and closures

Blocks created by `when`, `while`, and `repeat` share the surrounding scope. Function calls create a local scope.

```sprig
let name = "outside"
fn greet():
    let name = "inside"
    print(name)
end

greet()
print(name)
```

Output:

```text
inside
outside
```

The inner `name` shadows the outer `name`; it does not replace it.

A closure remembers variables from where it was defined:

```sprig
fn make_counter():
    let count = 0
    fn next():
        count = count + 1
        return count
    end
    return next
end

let counter = make_counter()
print(counter(), counter())
```

Output:

```text
1 2
```

The two calls update the same captured `count` variable.

## 7. Interactive prompt

Run `python3 sprig.py` without a file to open the prompt:

```text
sprig> 2 + 3
5
sprig> :reset
sprig> :quit
```

Use `end` to finish every open block. The prompt waits for more lines while a block is incomplete. `:reset` clears all variables and creates a fresh environment. `:quit` exits.

The prompt displays non-`nil` expression results. A file does not display a bare expression automatically, so use `print` in programs you save.

## 8. Error messages and what they mean

Sprig reports errors with a line number. In file mode, the interpreter also prints the filename and exits with status 1. The message tells you what to repair.

### `Unexpected character '@'`

The lexer found a character that is not part of Sprig syntax.

```sprig
print(@)
```

Fix: remove the character or replace it with a supported operator or name.

### `Unterminated string`

An opening double quote did not have a closing double quote on the same line.

```sprig
print("hello)
```

Fix: close the string: `print("hello")`. Sprig strings cannot span source lines.

### `Unknown escape \\x`

The string contains an escape sequence other than `\"`, `\\`, `\n`, `\t`, or `\r`.

```sprig
print("bad\\x")
```

Fix: use a supported escape or write the character without a backslash.

### `Expected token, got token`

The parser expected a particular punctuation mark, keyword, or delimiter and found something else. Common causes are a missing `:`, `)`, newline, or `end`.

```sprig
when true
    print("yes")
end
```

Fix: add the colon after the condition: `when true:`.

### `Expected a name`

A declaration, function, or parameter list needs an identifier, but the next token is a keyword or another kind of value.

```sprig
let when = true
```

Fix: choose a non-keyword name, such as `let ready = true`.

### `Expected 'end'`

The parser reached the end of the file while a `when`, `while`, `repeat`, or `fn` block was still open.

```sprig
while true:
    print("still open")
```

Fix: add the matching `end`. If the loop is real, also ensure its condition eventually becomes false.

### `Expected an expression, got '...'`

An operator, keyword, or punctuation mark appears where a value should begin.

```sprig
print(1 + )
```

Fix: put an expression after `+`, such as `print(1 + 2)`.

### `Use 'and' between comparisons`

Sprig does not allow chained comparisons.

```sprig
print(1 < score < 10)
```

Fix: write the two boolean comparisons explicitly:

```sprig
print(1 < score and score < 10)
```

### `Assignment needs a variable name`

The left side of `=` is not a bare name.

```sprig
(x) = 1
```

Fix: assign directly to a declared name: `x = 1`.

### `Return is only allowed inside a function`

`return` appears outside an `fn` body.

```sprig
return 1
```

Fix: move it inside a function, or use an expression/assignment at the top level.

### `Duplicate parameter 'x'`

A function lists the same parameter name more than once.

```sprig
fn pair(x, x):
end
```

Fix: give each parameter a different name.

### `Name 'x' is already declared`

`let` or `fn` is trying to create a name that already exists in the same scope.

```sprig
let score = 1
let score = 2
```

Fix: use assignment when you mean to change the value: `score = 2`.

### `Undefined name 'x'`

The program reads or assigns a name that has not been declared in an accessible scope.

```sprig
print(missing)
```

Fix: declare it first with `let` or `fn`, and check the spelling and capitalization.

### `Expected a boolean (true or false)`

`when`, `while`, `not`, `and`, or `or` received a value that is not a boolean.

```sprig
when 1:
    print("yes")
end
```

Fix: compare the value or use an actual boolean, for example `when score > 0:`.

### `Expected numbers`

Unary minus or an arithmetic operation received a non-number.

```sprig
print(-false)
```

Fix: use a number, or change the expression so it performs a boolean or string operation instead.

### `Expected numbers (or two strings for '+')`

An arithmetic operator received incompatible values, such as a string and a number.

```sprig
print("5" + 1)
```

Fix: use two numbers (`5 + 1`) or two strings (`"5" + "1"`).

### `Division by zero`

`/` or `%` received zero as its right operand.

```sprig
print(4 / 0)
```

Fix: check the divisor before performing the operation.

### `Repeat needs a non-negative integer`

The count in `repeat` is negative, a decimal number, a boolean, or another type.

```sprig
repeat 2.5:
end
```

Fix: use `repeat 2:` or calculate a value that is a non-negative integer.

### `Expected N arguments, got M`

A user-defined function was called with the wrong number of arguments.

```sprig
fn add(left, right):
    return left + right
end

print(add(1))
```

Fix: pass exactly two arguments, such as `add(1, 2)`.

### `Value is not a function`

The program used a number, string, boolean, nil, or another non-function value as a callee.

```sprig
let number = 4
print(number())
```

Fix: call a name that contains a function.

### `Number is too large`

An input number or arithmetic result is outside the finite range supported by the interpreter.

Fix: use smaller values or split the calculation into manageable steps.

### `Too much recursion or nesting`

The program recursed or nested calls more deeply than the Python runtime allows.

Fix: check the base case and make sure each recursive call moves toward it. A loop may be a better choice for a very deep computation.

### `Use a .sprig source file`

The command-line file argument does not end in `.sprig`.

Fix: rename the file or pass the path to a Sprig source file.

### `Unfinished block: expected 'end'`

The interactive prompt reached end-of-file while waiting for a closing `end`.

Fix: enter the missing `end` before closing the prompt.

## 9. A small complete example

This program uses declarations, assignment, a function, a condition, a loop, arithmetic, and output together:

```sprig
fn total_to(limit):
    let total = 0
    let current = 1
    while current <= limit:
        total = total + current
        current = current + 1
    end
    return total
end

let answer = total_to(5)
when answer == 15:
    print("Correct:", answer)
otherwise:
    print("Unexpected:", answer)
end
```

Output:

```text
Correct: 15
```

When a program behaves unexpectedly, read it from the top: check declarations, follow each assignment, check the condition before each branch or loop, and use the exact error message to find the first rule that was violated.
