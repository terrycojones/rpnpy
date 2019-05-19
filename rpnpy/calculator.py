from __future__ import print_function, division

import sys
import inspect
import math
import decimal
import operator
import functools
from pprint import pprint

try:
    import builtins
except ImportError:
    if sys.version_info < (3,):
        print('The calculator only runs under Python 3.', file=sys.stderr)
        sys.exit(1)
    else:
        raise

from rpnpy.inspect import countArgs
from rpnpy.io import splitInput
from rpnpy.errors import UnknownModifiersError, IncompatibleModifiersError


class Function:
    def __init__(self, moduleName, name, func, nArgs):
        self.moduleName = moduleName
        self.name = name
        self.func = func
        self.nArgs = nArgs

    def __call__(self, *args, **kw):
        return self.func(*args, **kw)

    def __repr__(self):
        return 'Function(%s (calls %s with %d arg%s))' % (
            self.name, self.path, self.nArgs, '' if self.nArgs == 1 else 's')

    @property
    def path(self):
        return '%s.%s' % (self.moduleName, self.name)


class Variable:
    def __init__(self, name, variables):
        self.name = name
        self._variables = variables

    def __repr__(self):
        return 'Variable(%s, current value: %r)' % (
            self.name, self._variables[self.name])


class Calculator:
    def __init__(self, separator=None, outfp=sys.stdout, errfp=sys.stderr,
                 debug=False):
        self._separator = separator
        self._outfp = outfp
        self._errfp = errfp
        self._debug = debug
        self.stack = []
        self._previousStack = self._previousVariables = None
        self._functions = {}
        self._variables = {}

        self.addSpecialCases()
        for module in math, operator, builtins, functools, decimal:
            self.importCallables(module)
        self.addAbbrevs()
        self.addConstants()

    def __len__(self):
        return len(self.stack)

    def report(self, *args, **kw):
        print(*args, file=self._outfp, **kw)

    def err(self, *args, **kw):
        print(*args, file=self._errfp, **kw)

    def debug(self, *args, **kw):
        if self._debug:
            print(*args, file=self._errfp, **kw)

    def pprint(self, *args, **kw):
        pprint(*args, stream=self._outfp, **kw)

    def register(self, func, name=None, nArgs=None, moduleName=None):
        name = name or func.__name__
        if name in self._functions:
            self.debug('Registering new functionality for already known '
                       'function named %r.' % name)

        moduleName = moduleName or 'calculator-registered-method'
        nArgs = countArgs(func) if nArgs is None else nArgs
        self._functions[name] = Function(moduleName, name, func, nArgs)

    def addAbbrevs(self):
        for longName, shortNames in (
                ('decimal.Decimal', ('Decimal',)),
                ('math.log', ('log',)),
                ('operator.add', ('+',)),
                ('operator.eq', ('==',)),
                ('operator.mul', ('*',)),
                ('operator.ne', ('!=',)),
                ('operator.sub', ('-',)),
                ('operator.truediv', ('/', 'div')),
                ('builtins.bool', ('bool',)),
                ('builtins.int', ('int',)),
                ('builtins.map', ('map',)),
                ('builtins.max', ('max',)),
                ('builtins.min', ('min',)),
                ('builtins.print', ('print',)),
                ('builtins.range', ('range',)),
                ('builtins.str', ('str',)),
                ('functools.reduce', ('reduce',)),
        ):
            try:
                function = self._functions[longName]
            except KeyError:
                self.err('Long function name %r is unknown' % longName)
            else:
                for shortName in shortNames:
                    if shortName not in self._functions:
                        # self.err('Long name %r alias %r' %
                        # (longName, shortName))
                        self._functions[shortName] = function
                    else:
                        self.report(shortName, 'already known')

    def addSpecialCases(self):
        """
        Add argument counts for functions that cannot have their signatures
        inspected.
        """
        for module, func, nArgs in (
                (math, math.log, 1),
                (builtins, builtins.bool, 1),
                (builtins, builtins.int, 1),
                (builtins, builtins.map, 2),
                (builtins, builtins.max, 1),
                (builtins, builtins.min, 1),
                (builtins, builtins.print, 1),
                (builtins, builtins.str, 1),
                (builtins, builtins.range, 1),
                (functools, functools.reduce, 2),
                (decimal, decimal.Decimal, 1),
        ):
            longName = '%s.%s' % (module.__name__, func.__name__)
            try:
                self._functions[longName]
            except KeyError:
                self._functions[longName] = Function(
                    module.__name__, func.__name__, func, nArgs)
            else:
                self.err('Long function name %r is already set' % longName)

    def addConstants(self):
        """Add some constants (well, constant in theory) from math"""
        constants = [
                ('e', math.e),
                ('inf', math.inf),
                ('nan', math.nan),
                ('pi', math.pi),
        ]

        if sys.version_info > (3, 5):
            constants.append(('tau', math.tau))

        for name, value in constants:
            if name in self._variables:
                self.err('%r is already a variable!' % name)
            else:
                self._variables[name] = value

    def importCallables(self, module):
        moduleName = module.__name__
        exec('import ' + moduleName, globals(), self._variables)
        callables = inspect.getmembers(module, callable)

        for name, func in callables:
            if name.startswith('_'):
                continue

            try:
                if issubclass(func, BaseException):
                    continue
            except TypeError:
                pass

            nArgs = countArgs(func)

            if nArgs is None:
                continue

            path = '%s.%s' % (moduleName, name)

            if path in self._functions:
                if path != 'decimal.Decimal':
                    self.err('Function %r already exists' % path)
                continue

            # Add the function to our functions dict along with a default
            # number of positional parameters it expects. This allows the
            # user to call it and have the arguments taken from the stack
            # (the number of arguments used can always be modified via
            # e.g., /3 on the command line).
            exec('self._functions["%s"] = Function("%s", "%s", %s, %d)' %
                 (path, moduleName, name, path, nArgs))

            # Import the function by name to allow the user to use it in a
            # command with an explicit argument, instead of applying it to
            # whatever is on the stack.
            if name in self._variables:
                self.debug('name %s already defined! Ignoring %s' %
                           (name, path))
            else:
                exec('from %s import %s' % (moduleName, name), globals(),
                     self._variables)
                if name not in self._variables:
                    self.err('name %s not now defined!!!' % name)
                assert name not in self._functions
                self._functions[name] = self._functions[path]

    def printStack(self, n=None):
        """
        Print the stack or some item(s) from it.

        @param n: Either an C{int} or a slice specifying what part
            of the stack to print.
        """
        if n is None:
            pprint(self.stack)
        else:
            try:
                pprint(self.stack[n])
            except IndexError:
                self.err(
                    'Cannot print stack item %d (stack has only %d item%s)' %
                    (n, len(self), '' if len(self) == 1 else 's'))

    def saveState(self):
        """Save the stack and variable state."""
        self._previousStack = self.stack.copy()
        self._previousVariables = self._variables.copy()

    def _finalize(self, result, modifiers, stateAlreadySaved=False):
        """Process the final result of executing a command.

        @param result: The result.
        @param modifiers: A C{Modifiers} instance.
        @param stateAlreadySaved: If C{True} the stack and variable state
            have already been saved in earlier processing of the command.
        """
        if modifiers.list:
            result = list(result)
        if modifiers.iterate:
            if modifiers.print:
                for i in result:
                    self.report(i)
            elif not modifiers.preserveStack:
                if not stateAlreadySaved:
                    self.saveState()
                self.stack.extend(result)
        else:
            if modifiers.print:
                self.report(result)
            elif not modifiers.preserveStack:
                if not stateAlreadySaved:
                    self.saveState()
                self.stack.append(result)

    def execute(self, line):
        """
        Execute a line of commands.

        @param line: A C{str} command line to run.
        """
        inputGen = splitInput(line, self._separator)

        try:
            while True:
                try:
                    command, modifiers, count = next(inputGen)
                except UnknownModifiersError as e:
                    self.err('Unknown modifiers: %s' % ', '.join(e.args))
                    return
                except IncompatibleModifiersError as e:
                    self.err('Incompatible modifiers: %s' % e.args[0])
                    return
                else:
                    self._executeOneCommand(command, modifiers, count)
        except StopIteration:
            return

    def _executeOneCommand(self, command, modifiers, count):
        """
        Execute one command.

        @param command: A C{str} command to run.
        @param modifiers: A C{Modifiers} instance.
        @param count: An C{int} count, or C{None} if no count was given.
        """
        if not command:
            self.debug('Empty command')
            return

        done = self._tryFunction(command, count, modifiers)

        if done is False and count is not None:
            self.err('Modifier count %d will not be used' % count)

        if done is False:
            done = self._tryVariable(command, modifiers)

        if done is False:
            done = self._trySpecial(command, modifiers)

        if done is False:
            done = self._tryEval(command, modifiers)

        if done is False:
            done = self._tryExec(command)

        if done is False:
            self.err('Could not execute %r!' % command)

    def _tryFunction(self, command, count, modifiers):
        if modifiers.forceCommand:
            return False

        try:
            function = self._functions[command]
        except KeyError:
            self.debug('%s is not a known function' % (command,))
            return False

        self.debug('Found function %r' % command)
        if count is None:
            nArgs = len(self) if modifiers.all else function.nArgs
        else:
            nArgs = int(count)
            if modifiers.all:
                if len(self) != nArgs:
                    self.err('/modifiers cannot have both a count and a *')
                    return

        if modifiers.push:
            self._finalize(function.func, modifiers)
        elif len(self) < function.nArgs:
            self.err(
                'Not enough args on stack! (%s needs %d arg%s, stack has '
                '%d item%s)' %
                (command, nArgs, '' if nArgs == 1 else 's',
                 len(self), '' if len(self) == 1 else 's'))
        else:
            args = []
            for arg in self.stack[-nArgs:]:
                if isinstance(arg, Function):
                    args.append(arg.func)
                elif isinstance(arg, Variable):
                    args.append(self._variables[arg.name])
                else:
                    args.append(arg)

            if not modifiers.preserveStack:
                self.saveState()
                self.stack = self.stack[:-nArgs]

            self.debug('Calling %s with %r' % (function.name, tuple(args)))
            try:
                result = function.func(*args)
            except Exception as e:
                self.err('Exception running %s(%s): %s' %
                         (function.name, ', '.join(map(str, args)), e))
                self._variables = self._previousVariables
                self.stack = self._previousStack
            else:
                self._finalize(
                    result, modifiers,
                    stateAlreadySaved=(not modifiers.preserveStack))

    def _tryVariable(self, command, modifiers):
        if modifiers.forceCommand:
            return False

        if command in self._variables:
            self._finalize(
                Variable(command, self._variables) if modifiers.push
                else self._variables[command], modifiers)
        else:
            return False

    def _trySpecial(self, command, modifiers):
        lcommand = command.lower()

        if lcommand == 'quit' or lcommand == 'q':
            raise EOFError()
        elif lcommand == 'pop':
            if self.stack:
                self.saveState()
                result = self.stack.pop()
                if modifiers.print:
                    self.pprint(result)
            else:
                self.err('Cannot pop (stack is empty)')
        elif lcommand == 'swap':
            if len(self) > 1:
                self.saveState()
                self.stack[-2:] = reversed(self.stack[-2:])
            else:
                self.err('Cannot swap (stack needs 2 items)')
        elif lcommand == 'functions':
            for name, func in sorted(self._functions.items()):
                self.report(name, func)
        elif lcommand == 'stack' or lcommand == 's' or lcommand == 'f':
            self.printStack()
        elif lcommand == 'variables' or lcommand == 'v':
            for name, value in sorted(self._variables.items()):
                self.report('%s: %r' % (name, value))
        elif lcommand == 'clear' or lcommand == 'c':
            if self.stack:
                if modifiers.preserveStack:
                    self.err('The /= modifier makes no sense with %s' %
                             command)
                else:
                    self.saveState()
                    self.stack = []
        elif lcommand == 'dup' or lcommand == 'd':
            if self.stack:
                if modifiers.preserveStack:
                    self.err('The /= modifier makes no sense with %s' %
                             command)
                else:
                    self._finalize(self.stack[-1], modifiers)
            else:
                self.err('Cannot duplicate (stack is empty)')
        elif lcommand == 'undo' or lcommand == 'u':
            if self._previousStack is None:
                self.err('Nothing to undo')
            elif modifiers.preserveStack:
                self.err('The /= modifier makes no sense with %s' %
                         command)
            elif modifiers.print:
                self.err('The /p modifier makes no sense with %s' %
                         command)
            else:
                self.stack = self._previousStack.copy()
                self._variables = self._previousVariables.copy()
        elif lcommand == 'print' or lcommand == 'p':
            self.printStack(-1)
        elif lcommand == 'none':
            self._finalize(None, modifiers)
        elif lcommand == 'true':
            self._finalize(True, modifiers)
        elif lcommand == 'false':
            self._finalize(False, modifiers)
        elif modifiers.forceCommand:
            self.err('Unknown command: %s' % command)
        else:
            return False

    def _tryEval(self, command, modifiers):
        try:
            value = eval(command, globals(), self._variables)
        except Exception as e:
            self.debug('Could not eval(%r): %s' % (command, e))
            return False
        else:
            self.debug('eval %s worked: %r' % (command, value))
            self._finalize(value, modifiers)

    def _tryExec(self, command):
        self.saveState()
        try:
            exec(command, globals(), self._variables)
        except Exception as e:
            self.err('Could not exec(%r): %s' % (command, e))
            self._variables = self._previousVariables
            self.stack = self._previousStack
            return False
        else:
            self.debug('exec worked.')
