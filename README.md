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
modifiers must follow a `:`.  The modifiers are a set of single letters and
may also include a single number. Hence, for example,

```
abs
```

is a simple command (apply the `abs` function to the value on the top of
the stack) with no modifiers, whereas

```
+ :p= 17
```

run the `+` command with modifiers (`p`, `=`, and `17`).

The full list of commands and modifiers is given below.

#### Whitespace

Leading and trailing whitespace in the command is ignored. Whitespace
anywhere in the modifiers is ignored.


## Operation via standard input

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

## REPL operation

In REPL mode, the calculator repeatedly prints a prompt, reads a command,
and executes it. For example:

```sh
$ rpn.py
--> 4
--> 5
--> +
--> p
9
```

you can change the prompt using `--prompt` on the command line.

## Commands

There are two kinds of commands: normal and special. 

## Modifiers
