# rpnpy - A reverse-Polish notation calculator for Python

The `rpn.py` script implements a reverse-Polish notation calculator for
Python. As well as providing for traditional numeric calculator operations,
you can put Python objects and functions onto the stack, etc.

## Usage

The calculator either works interactively from the shell using a
[read-eval-print loop](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)
(REPL) or will read commands from standard input.

### Command syntax

Input lines are either comments (first non-whitespace character on the line
is `#`) or are split into a command and optional modifiers. If given, the
modifiers must follow a `/`. Hence:

```
4
```

is a simple command (push the value `4` onto the stack) with no modifiers,
whereas

```
+ /3=
```

is the `+` command with two modifiers (the number `3` and the letter `=`).

The full list of commands and modifiers is given below.


### Via standard input

When reading from standard input, lines will be split on whitespace and
each field is treated as a separate command. This allows for simple
command-line usage such as

```sh
$ echo 4 5 + | rpn.py
9
```

If you have a file of commands you want to pipe into `rpn.py` you might
want to turn off this splitting:

```sh
$ cat data
4
5
# This is a comment
+


$ rpn.py < data
9
```

You can change the separator using `--separator`:

```sh
$ echo 4_5_+ | rpn.py --separator _
9
```

By default, the final calculator stack is printed when standard input is
exhausted:

```sh
$ echo 4 5 | rpn.py
[4, 5]
```

You can disable the final printing with `--noPrint`:

```sh
$ echo 4 5 | rpn.py --noPrint
```

in which case you can print things yourself using the `p` command (see
below).
