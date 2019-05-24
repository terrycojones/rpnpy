# rpn.py - a reverse-Polish notation calculator for Python

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
# Add two numbers. The stack is printed after all commands are run.
$ rpn.py 4 5 +
9

# Do the same thing, but read from standard input (all the commands below
# could also be run in this way).
$ echo 4 5 + | rpn.py
9

# Sine of 90 degrees (note that Python's sin function operates on
# radians). The commands are in quotes so the shell doesn't expand the '*'.
$ rpn.py '90 pi 180 / * sin'
1.0

# Same thing, different quoting.
$ rpn.py 90 pi 180 / \* sin
1.0

# Same thing, use 'mul' instead of '*'.
$ rpn.py 90 pi 180 / mul sin
1.0

# Area of a circle radius 10
$ rpn.py 'pi 10 10 * *'
314.1592653589793

# Equivalently, using ':2' to push 10 onto the stack twice.
$ rpn.py 'pi 10:2 * *'
314.1592653589793

# Equivalently, using 'dup' to duplicate the 10 and 'mul' instead of '*'
$ rpn.py pi 10 dup mul mul
314.1592653589793
```

### Function calling argument push order

On a regular RPN calculator you would do what we normally think of as an
[infix](https://en.wikipedia.org/wiki/Infix_notation) operation such as
`5 - 4` by pushing `5` onto the stack, then pushing `4`, and finally
running the `-` function. The operator is taken out of middle and given at
the end and the original infix order of the arguments is the order you push
them onto the stack. Of course this doesn't make any difference for
commutative operations like `+` and `*`, but is important for `/` and `-`.

In Python we have various functions like
[`map`](https://docs.python.org/3.5/library/functions.html#map),
[`filter`](https://docs.python.org/3.5/library/functions.html#filter),
[`functools.reduce`](https://docs.python.org/3.5/library/functools.html#functools.reduce),
and the long-ago deprecated Python 2
[`apply`](https://docs.python.org/2/library/functions.html#apply) function.
These are typically thought of as having a prefix or
[Polish notation](https://en.wikipedia.org/wiki/Polish_notation) signature,
accepting a function followed by an iterable. E.g.,
[`map(function, iterable)`](https://docs.python.org/3.5/library/functions.html#map).

To be consistent, with RPN argument pushing just described for the numeric
operations, in the case of (what we normally think of as) prefix functions
such as `map`, we should therefore push the function to be run, then push
the iterable, then call `map` (`reduce`, `filter`, etc).

Like this:

```sh
$ rpn.py 'str:! [6,7,8] map:i'
['6', '7', '8']
```

### Notes
1. Here the `:!` modifier causes the `str` function to be pushed onto the
   stack instead of being run, and the `:i` modifier causes the result of
   `map` to be iterated before being added to the stack.
1. When you run a function (like `map`, or `apply`) that needs a callable
   (or a function like `join` that needs a string) and you don't specify a
   count (using `:3` for example), `rpn.py` will search the stack for a
   suitable item and use the first one it finds. It doesn't really have a
   choice in this case because it doesn't know how many arguments the
   function (once it is found) will be applied to.  This should usually
   work just fine. You can always use an explicit count (like `:3`) if not.
   Note that this situation does not apply if you use the `:r` modifier
   (see below) because in that case the callable (or string, in the case of
   `join`) will be expected to be on the top of the stack (and its
   signature can then be examined to know how many arguments to pass it).

You might find it more natural to use `map` and friends the other way
around. I.e., first push the iterable, then push the function to be
applied, and then call `map`.  In that case, you can use the `:r` modifier
to tell the calculator to reverse the order of the arguments passed to a
function. In the following, we push in the other order and then use
`map:ir` (the `i` is just to iterate the `map` result to produce a list).

```sh
$ rpn.py '[6,7,8] str:! map:ir'
['6', '7', '8']
```

Continuing on the map theme, you could instead simply reverse part of the
stack before running a function:

```sh
$ rpn.py '[6,7,8] str:! reverse map:i'
['6', '7', '8']
```

The `reverse` command operates on two stack items by default, but it can
take a numeric argument or you can run it with the `:*` modifier which will
cause it to be run on the whole stack:

```sh
# Reverse the top 3 stack elements then reverse the whole of the stack.
$ rpn.py '5 6 7 8 reverse:3 reverse:*'
[6, 7, 8, 5]
```

### More examples

```sh
# The area of a circle again, but using reduce to do the multiplying.  The
# ':!' modifier tells rpn.py to push the '*' function onto the stack
# instead of immediately running it.
$ rpn.py '*:! [pi,10,10] reduce'
314.1592653589793

# Same thing, but push the numbers individually onto the stack, then the
# ':3' tells reduce to iterate over three stack items. Use 'mul' as an
# alternative to '*'.
$ rpn.py 'pi 10 dup mul:! reduce:3'
314.1592653589793

# Equivalently, using ':*' to tell reduce to use the whole stack.
$ rpn.py 'pi 10 dup *:! reduce:*'
314.1592653589793

# Push 'True' onto the stack 5 times, turn the whole stack ('*') into a
# list and print it ('p'), then pass that list to 'sum'.
$ rpn.py 'True:5 list:*p sum'
[True, True, True, True, True]
5

# Here's something a bit more long-winded (and totally pointless):
#
# Push 0..9 onto the stack
# call Python's 'reversed' function
# push the 'str' function
# use 'map' to convert the list of digits to strings
# join the string digits with the empty string
# convert the result to an int
# take the square root
# push 3 onto the stack
# swap the top two stack elements
# call 'round' to round the result to three decimal places
#
# the ':i' modifier (used here twice) causes the value from the command
# to be iterated and the result to be put on the stack as a single list.
# It's a convenient way to iterate over a generator, a range, a map,
# dictionary keys, etc.
$ rpn.py 'range(10):i reversed str:! map:i "" join int sqrt 3 swap round:2'
9876543210
```

You could do that last one in Python with a bunch of parens:

```python
from math import sqrt
print(round(sqrt(int(''.join(map(str, reversed(range(10)))))), 3))
```

The elimination of parens is the main beauty of RPN (at least
esthetically - the stack model of computation is a pretty awesome idea
too). The price is that you have to learn to think in postfix. On that
subject, I could have pushed the `3` (the number of decimal places to round
to) onto the stack at the very start of the last `rpn.py` command above,
but I didn't think that far ahead, so I pushed it at the end and then
called `swap` to swap around the top two stack elements. I.e., this works
too:

```sh
$ rpn.py '3 range(10):i reversed str:! map:i "" join int sqrt round:2'
99380.799
```

There's another way to skin this cat, using the `:r` modifier, which
reverses the order of the arguments being passed to a function. So instead
of putting the `3` out front or putting it at the end and then calling
`swap` (as I did originally), we can just ask for the arguments to be
passed to round the other way around.

```sh
$ rpn.py 'range(10):i reversed str:! map:i "" join int sqrt 3 round:2r'
99380.799
```


More involved calculations can be done in an interactive REPL session:

```sh
# REPL usage, with automatic splitting of whitespace turned off
# (so we give one command per line).
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
    r: reverse
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
* Add an `r` modifier to reverse the order of args to a function call.
* Outlaw zero count.

## Thanks

To [David Pattinson (@davipatti)](https://github.com/davipatti) for various
nice ideas, including executing the command line arguments.
