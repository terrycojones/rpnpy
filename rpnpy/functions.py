def apply(calc, modifiers, nargs):
    """Apply a function to some arguments.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param nargs: An C{int} count of the number of arguments to pass.
    """
    if nargs is None:
        nargs = len(calc) - 1 if modifiers.all else 1

    nargsAvail = len(calc) - 1
    if nargsAvail < nargs:
        calc.err('Cannot call apply with %d argument%s '
                 '(stack has only %d item%s available)' %
                 (nargs, '' if nargs == 1 else 's',
                  nargsAvail, '' if nargsAvail == 1 else 's'))
        return

    func = calc.stack[-1]
    if not callable(func):
        calc.err('Top stack item is not callable, cannot run apply')
        return

    args = calc.stack[-(nargs + 1):-1]
    calc._finalize(func(*args), modifiers, nPop=nargs + 1)
