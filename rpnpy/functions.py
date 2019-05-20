import functools

# IMPORTANT
#
# If you add a special functions here:
#
#   1. It must have a calc, modifiers, count signature.
#   2. You must give it a tuple of names (see examples below).
#   3. You must add it to FUNCTIONS, at bottom.
#
# That is all.


def quit(calc, modifiers, count):
    """Quit the calculator.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    raise EOFError()


quit.names = ('quit', 'q')


def functions(calc, modifiers, count):
    """List all known functions

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    for name, func in sorted(calc._functions.items()):
        calc.report(name, func)


functions.names = ('functions',)


def stack(calc, modifiers, count):
    """Print the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    calc.printStack()


stack.names = ('stack', 's', 'f')


def variables(calc, modifiers, count):
    """Show all variables.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    for name, value in sorted(calc._variables.items()):
        calc.report('%s: %r' % (name, value))


variables.names = ('variables', 'v')


def clear(calc, modifiers, count):
    """

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    if calc.stack:
        if modifiers.preserveStack:
            calc.err('The /= modifier makes no sense with clear')
        else:
            calc._finalize(None, nPop=len(calc), modifiers=modifiers,
                           noValue=True)


clear.names = ('clear', 'c')


def dup(calc, modifiers, count):
    """Duplicate the top of stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    if calc.stack:
        if modifiers.preserveStack:
            calc.err('The /= modifier makes no sense with dup')
        else:
            calc._finalize(calc.stack[-1], modifiers)
    else:
        calc.err('Cannot duplicate (stack is empty)')


dup.names = ('dup', 'd')


def undo(calc, modifiers, _):
    """Undo the last operation.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    """
    if calc._previousStack is None:
        calc.err('No undo saved')
    elif modifiers.preserveStack:
        calc.err('The /= modifier makes no sense with undo')
    elif modifiers.print:
        calc.err('The /p modifier makes no sense with undo')
    else:
        calc.stack = calc._previousStack.copy()
        calc._variables = calc._previousVariables.copy()


undo.names = ('undo', 'u')


def print_(calc, _, __):
    """Print the top of stack.

    @param calc: A C{Calculator} instance.
    """
    calc.printStack(-1)


print_.names = ('print', 'p')


def apply(calc, modifiers, count):
    """Apply a function to some arguments.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    if count is None:
        count = len(calc) - 1 if modifiers.all else 1

    nargsAvail = len(calc) - 1
    if nargsAvail < count:
        calc.err('Cannot call apply with %d argument%s '
                 '(stack has only %d item%s available)' %
                 (count, '' if count == 1 else 's',
                  nargsAvail, '' if nargsAvail == 1 else 's'))
        return

    func = calc.stack[-1]
    if not callable(func):
        calc.err('Top stack item (%r) is not callable' % func)
        return

    args = calc.stack[-(count + 1):-1]
    calc._finalize(func(*args), modifiers, nPop=count + 1)


apply.names = ('apply',)


def reduce(calc, modifiers, count):
    """Apply a function to some arguments using reduce.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    if count is None:
        count = len(calc) - 1 if modifiers.all else 1

    nargsAvail = len(calc) - 1
    if nargsAvail < count:
        calc.err('Cannot call reduce with %d argument%s '
                 '(stack has only %d item%s available)' %
                 (count, '' if count == 1 else 's',
                  nargsAvail, '' if nargsAvail == 1 else 's'))
        return

    func = calc.stack[-1]
    if not callable(func):
        calc.err('Top stack item (%r) is not callable' % func)
        return

    if count == 1:
        # Run on the first stack item after the function (which will
        # obviously need to be iterable).
        args = calc.stack[-2]
    else:
        # Collect several stack items into a list and run on that list.
        args = calc.stack[-(count + 1):-1]

    calc._finalize(functools.reduce(func, args), modifiers, nPop=count + 1)


reduce.names = ('reduce',)


def pop(calc, modifiers, count):
    """Pop some number of arguments (default 1) off the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    nArgs = (len(calc) if modifiers.all else 1) if count is None else count
    if len(calc) >= nArgs:
        value = calc.stack[-1] if nArgs == 1 else calc.stack[-nArgs:]
        calc._finalize(value, modifiers, nPop=nArgs, noValue=True)
    else:
        calc.err('Cannot pop %d item%s (stack length is %d)' %
                 (nArgs, '' if nArgs == 1 else 's', len(calc)))


pop.names = ('pop',)


def swap(calc, modifiers, _):
    """Swap the top two items on the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    """
    if len(calc) > 1:
        calc._finalize(reversed(calc.stack[-2:]), modifiers=modifiers,
                       nPop=2, extend=True)
    else:
        calc.err('Cannot swap (stack needs 2 items)')


swap.names = ('swap',)


def list_(calc, modifiers, count):
    """Convert some stack items into a list.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of stack items to make into
        a list.
    """
    if modifiers.push:
        calc._finalize(list, modifiers=modifiers)
    elif calc.stack:
        count = (len(calc) if modifiers.all else 1) if count is None else count
        if count == 1:
            value = calc.stack[-1]
            try:
                iterator = iter(value)
            except TypeError:
                value = [value]
            else:
                value = list(iterator)
        else:
            if len(calc) >= count:
                value = calc.stack[-count:]
            else:
                calc.err('Cannot list %d item%s (stack length is %d)' %
                         (count, '' if count == 1 else 's', len(calc)))
                return
        calc._finalize(value, modifiers=modifiers, nPop=count)
    else:
        calc.err('Cannot run list (stack is empty)')


list_.names = ('list',)


FUNCTIONS = (
    apply, clear, dup, functions, list_, pop, print_, quit, reduce, stack,
    swap, undo, variables)


def addSpecialFunctions(calc):
    """Add functions defined above

    @param calc: A C{Calculator} instance.
    """
    for func in FUNCTIONS:
        names = getattr(func, 'names')
        for name in names:
            calc.debug('Adding special command %r for %s' % (name, func))
            calc.registerSpecial(func, name)
