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
is `#`) or specify a command (or commands) followed by optional modifiers.
A command with no modifiers is `abs`, which will apply the `abs` function
to the value on the top of the stack.

If given, modifiers must follow a `:`.  The modifiers are a set of single
letters and may also include a single number. The input `+ :p= 17` causes
the `+` command to be executed, with modifiers `p`, `=`, and `17`.  The
full list of commands and modifiers is given below.

If modifiers are given, they apply to all commands on an input line.

#### Input line splitting

By default, `rpn.py` will split lines on whitespace and each field will be
taken as a command. Hence:

```sh
$ rpn.py
--> 4 5 +
```

will push `4` and then `5` onto the stack and then replace those two values
by their sum.

`rpn.py` prints the `--> ` as its prompt (see the <a href="#repl">REPL
section</a> below).

In many cases it is easy to avoid using spaces and inadvertently having
your input interpreted as multiple commands. For example, push a list onto
the stack:

```sh
$ rpn.py
--> [1,2,3]
```

but if you try that with embedded spaces, you'll an error:

```sh
$ rpn.py
--> [1, 2, 3]
Could not exec('[1,'): unexpected EOF while parsing (<string>, line 1)
No action taken on input '[1,'
Could not exec('3]'): invalid syntax (<string>, line 1)
No action taken on input '3]'
```

this is easily avoided with the `:n` (no split) modifier:

```sh
$ rpn.py
--> [1, 2, 3] :n
```

If you want `rpn.py` not to split lines into multiple commands, run with
the `--noSplit` command-line option. You can then use `:s` (split) if you
instead want to write an input line that should be split. Hence:

```sh
$ rpn.py --noSplit
--> [1, 2, 3]
--> 4 5 :s
```

the above will first push the list `[1, 2, 3]` onto the stack, and then `4`
and `5` will be split (on whitespace) and treated as two separate commands.

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

<a id="repl"></a>
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
