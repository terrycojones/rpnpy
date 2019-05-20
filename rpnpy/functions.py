import functools


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
        # Run on the top of the stack (which will need to be iterable).
        args = calc.stack[-1]
    else:
        # Collect several stack items into a list and run on that list.
        args = calc.stack[-count:-1]

    calc._finalize(functools.reduce(func, args), modifiers, nPop=count + 1)
