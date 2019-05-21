# rpn.py - A reverse-Polish notation calculator for Python

Here is `rpn.py`, a script implementing a
[reverse-Polish notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation)
(RPN) calculator for Python.

As well as providing for traditional numeric calculator operations, it
provides easy access to many Python functions, and you can put Python
objects and functions onto the stack and operate on them.

I wrote this for 3 reasons:

1.  I absolutely loved the [HP-41C](https://en.wikipedia.org/wiki/HP-41C)
    programmable calculator series, which used RPN. Although I had taught
    myself to program on a
    [Casio FX-502P](https://en.wikipedia.org/wiki/Casio_FX-502P_series) in
    1978, the Casio was like a toy compared to the HP-41C. I owned a 41C, a
    41CV, and then a 41CX, had a bunch of memory expansion packs, several
    other add-on packs (e.g., stats), a card reader/writer, and got it
    overclocked by some hardware hacker friends. It was an amazing machine.
    I still have one.
1.  I have been using the [UNIX](https://en.wikipedia.org/wiki/Unix)
    [dc](https://en.wikipedia.org/wiki/Dc_(computer_program)) (desk
    calculator) command on almost a daily basis since 1983 or so. `dc` is
    ancient (in UNIX terms), predating even
    [the C programming language](https://en.wikipedia.org/wiki/C_(programming_language)). `dc`
    provides a minimalist and rather cryptic RPN calculator. You can even
    program it, if you have a taste for mystery.  Here's a program I wrote
    in 1984 to factor numbers:

        [[neither]plsx]sn[c2pla2/sallx]se[ladv1+sm0=nla1=ncla2=pla2%0=elfx]sl
        [ldlm<pclald%0=cld2+sdlfx]sf[lap[is prime.]plsx]sp[ldplald/salfx]sc
        [[enter X : ]P?dsa0>n3sdllx]ss[[negative]plsx]snlsx

    [That code](https://gist.github.com/terrycojones/bdc16bf8910ba16dd2dd6ccab8cd7e53)
    still runs today, 35 years later, totally unchanged:
    
        $ dc factor
        enter X : 77
        7
        11
        is prime.
        enter X : 887
        887
        is prime.
    
    But `dc` has only a tiny set of operations. So while it's great to be
    able to easily use it from the command line (e.g., `echo 4 5 + p | dc`)
    I often find myself reaching for a real calculator or go into an
    interactive session with a full programming language (Perl, Python,
    etc).
1. I was curious what it would be like to have a Python RPN calculator that
   offered both the minimalist syntax of `dc` but that also offered a much
   wider range of operations and made it possible to put Python objects
   (lists, dicts, functions, etc.) onto the stack and operate on them. I'm
   curious what use I'll make of it, and what others might do with it too.

*Note* that this is a work in progress! Everything may change. Suggestions
 very welcome.

## Example rpn.py sessions

Before getting a bit more formal (and boring) in describing how you use
`rpn.py`, here are some example sessions to give you a flavor.

```sh
# Add two numbers. The stack is printed on exit when reading from stdin.
$ echo 4 5 + | rpn.py
9

# Sine of 90 degrees (Python's sin function operates on radians).
$ echo '90 pi 180 / * sin' | rpn.py
1.0
9

# Area of a circle radius 10
$ echo 'pi 10 10 * *' | rpn.py
314.1592653589793

# Equivalently, using ':2' to push 10 onto the stack twice.
echo 'pi 10:2 * *' | rpn.py
314.1592653589793

# Equivalently, using 'dup' to duplicate the 10.
echo 'pi 10 dup * *' | rpn.py
314.1592653589793

# Equivalently, using reduce to do the multiplying.  The ':!' modifier
# tells rpn.py to push the '*' function onto the stack instead of
# immediately running it.
echo '[pi,10,10] *:! reduce' | rpn.py
314.1592653589793

# Same thing, but push the numbers individually onto the stack, then the
# ':3' tells reduce to iterate over three stack items. Use 'mul' as an
# alternative to '*'.
echo 'pi 10 dup mul:! reduce:3' | rpn.py
314.1592653589793

# Equivalently, using ':*' to tell reduce to use the whole stack.
echo 'pi 10 dup *:! reduce:*' | rpn.py
314.1592653589793
```

```sh
# REPL usage, with automatic line-splitting off (so one command per line)
$ rpn.py --noSplit
--> 4
--> 5
--> 6
--> stack
[4, 5, 6]
--> f  # f is an alias for 'stack', as in dc.
[4, 5, 6]
--> clear  # Or just 'c'
--> f
[]
--> from numpy import log2
--> 32
--> log2
--> p
5.0
--> {'a':6, 'b':10, 'c':15}
--> len
--> p
3
--> [6,7,8]
--> str :!
--> f
[[6, 7, 8], <class 'str'>]
--> swap
--> f
[<class 'str'>, [6, 7, 8]]
--> map :i
--> f
['6', '7', '8']
```

```sh
$ rpn.py --noSplit
--> def celcius(f): return (f - 32) / 1.8
--> 212
--> celcius
--> f
[212, <function celcius at 0x7fc975055f28>]
--> apply :p
100.0

$ rpn.py --noSplit
--> 212
--> lambda f: (f - 32) / 1.8
--> apply :p
100.0
```

## Usage

The calculator either works interactively from the shell using a
[read-eval-print loop](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)
(REPL) or will read commands from standard input.

### Command syntax

Input lines are either comments (first non-whitespace character on the line
is `#`) or specify a command (or commands) followed by optional modifiers.

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

but if you try that with embedded spaces, you'll get an error:

```sh
$ rpn.py
--> [1, 2, 3]
Could not exec('[1,'): unexpected EOF while parsing (<string>, line 1)
No action taken on input '[1,'
Could not exec('3]'): invalid syntax (<string>, line 1)
No action taken on input '3]'
```

this can be avoided with the `:n` (no split) modifier, but note that the
modifier will only affect then next (and subsequent) lines. You can just
give an empty command with the ':n' modifier to toggle to no line
splitting:

```sh
$ rpn.py
--> :n  # no splitting of subsequent lines
--> [1, 2, 3]
```

If you want `rpn.py` not to split lines into multiple commands by default,
run with the `--noSplit` command-line option. You can then use `:s` (split)
if you instead want to switch to writing input lines that should be
split. Hence:

```sh
$ rpn.py --noSplit
--> [1, 2, 3]
--> :s  # split subsequent lines
--> 4 5
```

the above will first push the list `[1, 2, 3]` onto the stack, then toggle
to line splitting, and then `4` and `5` will be split (on whitespace),
treated as two separate commands, and result in two more values being
pushed onto the stack.

#### Whitespace

Leading and trailing whitespace in the command is ignored. Whitespace
anywhere in the modifiers is ignored (unless line splitting is on, in which
case you will get errors).

## Operation via standard input

When reading from standard input, the lines will be split on whitespace and
each field is treated as a separate command. This allows for simple
command-line usage such as

```sh
$ echo 4 5 + | rpn.py
9
```

For convenience, modifiers can be preceded by whitespace:

```sh
$ echo 100 log10 :! apply | rpn.py
2.0
```

In the above, the `:!` modifier applies to the preceding `log10` function
(causing it to be pushed onto the stack).

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
--> 4 5 +
--> p
9
```

you can change the prompt using `--prompt` on the command line.

## Commands

There are two kinds of commands: normal and special. 

### Special commands

    apply, clear, dup, functions, list, pop, print, quit, reduce, stack,
    swap, undo, variables

## Modifiers

```
    *: all
    c: forceCommand
    D: debug
    i: iterate
    n: noSplit
    =: preserveStack
    p: print
    !: push
    s: split
```

## History

`rpn.py` makes use of Python's
[readline](https://docs.python.org/3.7/library/readline.html) library to
allow familiar/comfortable command line editing. Your input history will be
saved to `~/.pycalc_history` if your version of readline has the
`append_history_file` command (present only in Python >= 3.6)?

## Todo

* Add direct access to functionality from [numpy](https://www.numpy.org/).
* Read start-up file of user-defined functions.

## Thanks

To [David Pattinson (@davipatti)](https://github.com/davipatti) for various
nice ideas, including executing the command line arguments.
