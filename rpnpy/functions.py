import functools

from rpnpy.errors import CalculatorError

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
    return calc.NO_VALUE


functions.names = ('functions',)


def stack(calc, modifiers, count):
    """Print the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    calc.printStack()
    return calc.NO_VALUE


stack.names = ('stack', 's', 'f')


def variables(calc, modifiers, count):
    """Show all variables.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    for name, value in sorted(calc._variables.items()):
        calc.report('%s: %r' % (name, value))
    return calc.NO_VALUE


variables.names = ('variables',)


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
    return calc.NO_VALUE


clear.names = ('clear', 'c')


def dup(calc, modifiers, count):
    """Duplicate the top of stack a number of times.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    if calc.stack:
        if modifiers.preserveStack:
            raise CalculatorError('The /= modifier makes no sense with dup')

        count = 1 if count is None else count
        value = calc.stack[-1]
        calc._finalize(value, modifiers, repeat=count)
        return value

    raise CalculatorError('Cannot duplicate (stack is empty)')


dup.names = ('dup', 'd')


def undo(calc, modifiers, _):
    """Undo the last operation.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    """
    if calc._previousStack is None:
        raise CalculatorError('No undo saved')

    if modifiers.preserveStack:
        raise CalculatorError('The /= modifier makes no sense with undo')

    if modifiers.print:
        raise CalculatorError('The /p modifier makes no sense with undo')

    calc.stack = calc._previousStack.copy()
    calc._variables = calc._previousVariables.copy()
    return calc.NO_VALUE


undo.names = ('undo',)


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
    func, args = calc.findCallableAndArgs('apply', modifiers, count)
    result = func(*args)
    calc._finalize(result, modifiers, nPop=len(args) + 1)
    return result


apply.names = ('apply',)


def join(calc, modifiers, count):
    """Join some stack items into a single string.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    sep, args = calc.findStringAndArgs('join', modifiers, count)
    nPop = len(args) + 1
    if len(args) == 1:
        # Only one argument from the stack, so run join on the value of
        # that stack item rather than on a list with just that one stack
        # item. Of course the stack item will need to be iterable or this
        # will fail (as it should).
        args = args[0]
    result = sep.join(map(str, args))
    calc._finalize(result, modifiers, nPop=nPop)
    return result


join.names = ('join',)


def reduce(calc, modifiers, count):
    """Apply a function to some arguments using reduce.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    func, args = calc.findCallableAndArgs('apply', modifiers, count)
    nPop = len(args) + 1
    if len(args) == 1:
        # Only one argument from the stack, so run reduce on the value of
        # that stack item rather than on a list with just that one stack
        # item. Of course the stack item will need to be iterable or this
        # will fail (as it should).
        args = args[0]
    value = functools.reduce(func, args)
    calc._finalize(value, modifiers, nPop=nPop)
    return value


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
        return value

    raise CalculatorError('Cannot pop %d item%s (stack length is %d)' %
                          (nArgs, '' if nArgs == 1 else 's', len(calc)))


pop.names = ('pop',)


def reverse(calc, modifiers, count):
    """Reverse some number of arguments (default 2) on the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    nArgs = (len(calc) if modifiers.all else 2) if count is None else count
    if len(calc) >= nArgs:
        if nArgs > 1:
            value = calc.stack[-nArgs:][::-1]
            calc._finalize(value, modifiers, nPop=nArgs, extend=True)
            return value

    raise CalculatorError('Cannot reverse %d item%s (stack length is %d)' %
                          (nArgs, '' if nArgs == 1 else 's', len(calc)))


reverse.names = ('reverse',)


def swap(calc, modifiers, _):
    """Swap the top two items on the stack.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    """
    if len(calc) > 1:
        calc._finalize(calc.stack[-2:][::-1], modifiers=modifiers,
                       nPop=2, extend=True)
        return calc.NO_VALUE

    raise CalculatorError('Cannot swap (stack needs 2 items)')


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
        return list

    if calc.stack:
        nArgs = (len(calc) if modifiers.all else 1) if count is None else count
        if nArgs == 1:
            value = calc.stack[-1]
            try:
                iterator = iter(value)
            except TypeError:
                value = [value]
            else:
                value = list(iterator)
        else:
            if len(calc) >= nArgs:
                value = calc.stack[-nArgs:]
            else:
                raise CalculatorError(
                    'Cannot list %d item%s (stack length is %d)' %
                    (nArgs, '' if nArgs == 1 else 's', len(calc)))
        calc._finalize(value, modifiers=modifiers, nPop=nArgs)
        return value

    raise CalculatorError('Cannot run list (stack is empty)')


list_.names = ('list',)


def map_(calc, modifiers, count):
    """Map a function over some arguments.

    @param calc: A C{Calculator} instance.
    @param modifiers: A C{Modifiers} instance.
    @param count: An C{int} count of the number of arguments to pass.
    """
    func, args = calc.findCallableAndArgs('map', modifiers, count)
    nPop = len(args) + 1
    if len(args) == 1:
        # Only one argument from the stack, so run map on the value of
        # that stack item rather than on a list with just that one stack
        # item. Of course the stack item will need to be iterable or this
        # will fail (as it should).
        args = args[0]
        extend = False
    else:
        extend = True
    result = map(func, args)
    calc._finalize(result, modifiers, extend=extend, nPop=nPop)
    return result


map_.names = ('map',)


FUNCTIONS = (
    apply,
    clear,
    dup,
    functions,
    join,
    list_,
    map_,
    pop,
    print_,
    quit,
    reduce,
    reverse,
    stack,
    swap,
    undo,
    variables,
)


def addSpecialFunctions(calc):
    """Add functions defined above

    @param calc: A C{Calculator} instance.
    """
    for func in FUNCTIONS:
        names = getattr(func, 'names')
        for name in names:
            calc.debug('Adding special command %r for %s' % (name, func))
            calc.registerSpecial(func, name)
