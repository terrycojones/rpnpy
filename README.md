# rpnpy - A reverse-Polish notation calculator for Python

Here is `rpn.py`, a script implementing a
[reverse-Polish notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation)
(RPN) calculator for Python.

As well as providing for traditional numeric calculator operations, you can
put Python objects and functions onto the stack and operate on them.

I wrote this for 3 reasons:

1.  I absolutely loved the [HP-41C](https://en.wikipedia.org/wiki/HP-41C)
    programmable calculator series, which used RPN. Although I had taught
    myself to program on a
    [Casio FX-502P](https://en.wikipedia.org/wiki/Casio_FX-502P_series) in
    1978, the Casio was like a toy compared to the HP-41C. I owned a 41C, a
    41CV, and then a 41CX, had a bunch of memory expansion packs, several
    other add-on packs (e.g., stats), a card reader/writer, and got it
    overclocked by some hardware hacker friends. It was an amazing
    machine. I still have one but don't use it.
1.  I have been using the [UNIX](https://en.wikipedia.org/wiki/Unix)
    [dc](https://en.wikipedia.org/wiki/Dc_(computer_program)) (desk
    calculator) command on almost a daily basis since 1983 or so. `dc` is
    ancient (in UNIX terms), predating even
    [the C programming language](https://en.wikipedia.org/wiki/C_(programming_language)). `dc`
    provides a minimalist and rather cryptic RPN calculator. You can program
    it, if you have a taste for mystery.  Here's a program I wrote in about
    1984 to factor numbers:

        [[neither]plsx]sn[c2pla2/sallx]se[ladv1+sm0=nla1=ncla2=pla2%0=elfx]sl
        [ldlm<pclald%0=cld2+sdlfx]sf[lap[is prime.]plsx]sp[ldplald/salfx]sc
        [[enter X : ]P?dsa0>n3sdllx]ss[[negative]plsx]snlsx

    [That code](https://gist.github.com/terrycojones/bdc16bf8910ba16dd2dd6ccab8cd7e53)
    still runs today, 35 years later, totally unchanged:
    
        $ dc factor
        enter X : 34
        2
        17
        is prime.
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
```

```sh
# REPL usage
$ rpn.py
--> 4 5 6
--> stack
[4, 5, 6]
--> f
[4, 5, 6]
--> clear
--> f
[]
--> from numpy import log2 :n
--> 32
--> log2 :p
5.0
--> {'a':6, 'b':10, 'c':15} :n
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

this can be avoided with the `:n` (no split) modifier:

```sh
$ rpn.py
--> [1, 2, 3] :n
```

If you want `rpn.py` not to split lines into multiple commands at all, run
with the `--noSplit` command-line option. You can then use `:s` (split) if
you instead want to write an input line that should be split. Hence:

```sh
$ rpn.py --noSplit
--> [1, 2, 3]
--> 4 5 :s
```

the above will first push the list `[1, 2, 3]` onto the stack, and then `4`
and `5` will be split (on whitespace), treated as two separate commands,
and result in two more values being pushed onto the stack.

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
--> 4 5 +
--> p
9
```

you can change the prompt using `--prompt` on the command line.

## Commands

There are two kinds of commands: normal and special. 

## Modifiers
