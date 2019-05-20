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

from rpnpy.functions import addSpecialFunctions
from rpnpy.inspect import countArgs
from rpnpy.io import findCommands
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

    OVERRIDES = set('builtins.list builtins.quit functools.reduce'.split())

    def __init__(self, splitLines=True, separator=None, outfp=sys.stdout,
                 errfp=sys.stderr, debug=False):
        self._splitLines = splitLines
        self._separator = separator
        self._outfp = outfp
        self._errfp = errfp
        self._debug = debug
        self.stack = []
        self._previousStack = self._previousVariables = None
        self._functions = {}
        self._special = {}
        self._variables = {}

        self.addSpecialCases()
        addSpecialFunctions(self)
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

    def batch(self, fp, print_=False):
        """Non-interactively read and execute commands from a file.

        @param fp: An iterator to read commands from.
        @param print_: If C{True}, print the stack after all commands are run.
        """
        for line in fp:
            try:
                self.execute(line)
            except EOFError:
                break
        if print_ and self.stack:
            self.printStack(-1 if len(self) == 1 else None)

    def repl(self, prompt):
        """Interactive read-eval-print loop.

        @param prompt: The C{str} prompt to print at the start of each line.
        """
        while True:
            try:
                try:
                    line = input(prompt)
                except ValueError as e:
                    if str(e) == 'I/O operation on closed file.':
                        # The user may have typed 'quit()'.
                        self.report()
                        break
                    else:
                        raise
                else:
                    self.execute(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                self.report()
                break

    def registerSpecial(self, func, name):
        self._special[name] = func

    def register(self, func, name=None, nArgs=None, moduleName=None):
        name = name or func.__name__
        if name in self._functions:
            self.debug('Registering new functionality for already known '
                       'function named %r.' % name)

        moduleName = moduleName or 'calculator-registered-method'
        nArgs = countArgs(func, 1) if nArgs is None else nArgs
        self._functions[name] = Function(moduleName, name, func, nArgs)

    def addAbbrevs(self):
        for longName, shortNames in (
                ('decimal.Decimal', ('Decimal',)),
                ('math.log', ('log',)),
                ('operator.attrgetter', ('attrgetter',)),
                ('operator.itemgetter', ('itemgetter',)),
                ('operator.methodcaller', ('methodcaller',)),
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
                (decimal, decimal.Decimal, 1),
                (operator, operator.attrgetter, 1),
                (operator, operator.itemgetter, 1),
                (operator, operator.methodcaller, 1),
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
            ('pi', math.pi)
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

            if path in self.OVERRIDES:
                self.debug('Not importing %r' % path)
                continue

            if path in self._functions:
                if path != 'decimal.Decimal':
                    self.err('Function %r already exists' % path)
                continue

            # Add the function to our functions dict along with a default
            # number of positional parameters it expects. This allows the
            # user to call it and have the arguments taken from the stack
            # (the number of arguments used can always be specified on the
            # command line (e.g., :3)
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
            self.pprint(self.stack)
        else:
            try:
                self.pprint(self.stack[n])
            except IndexError:
                self.err(
                    'Cannot print stack item %d (stack has only %d item%s)' %
                    (n, len(self), '' if len(self) == 1 else 's'))

    def saveState(self):
        """Save the stack and variable state."""
        self._previousStack = self.stack.copy()
        self._previousVariables = self._variables.copy()

    def _finalize(self, result, modifiers, nPop=0, extend=False,
                  repeat=1, noValue=False):
        """Process the final result of executing a command.

        @param result: A C{list} or C{tuple} of results to add to the stack.
        @param modifiers: A C{Modifiers} instance.
        @param nPop: An C{int} number of stack items to pop.
        @param extend: If C{True}, use extend to add items to the end of the
            stack, else use append.
        @param repeat: An C{int} number of times to add result to the stack.
        @param noValue: If C{True}, do not push any value (i.e., ignore
            C{result}).
        """
        if (nPop or not noValue) and not modifiers.preserveStack:
            # We're going to pop and/or push.
            self.saveState()
            if nPop:
                self.stack[-nPop:] = []

        if modifiers.iterate:
            try:
                iterator = iter(result)
            except TypeError:
                pass
            else:
                print('b4', result)
                result = list(iterator)
                print('af', result)

        if not (modifiers.preserveStack or noValue):
            add = self.stack.extend if extend else self.stack.append
            for _ in range(repeat):
                add(result)

        if modifiers.print:
            self.printStack(-1)

    def execute(self, line):
        """
        Execute a line of commands. Stop executing commands on any error.

        @param line: A C{str} command line to run.
        @return: A C{bool} indicating if all commands ran without error.
        """
        self.debug('Executing', line[:-1])
        commands = findCommands(line, self._splitLines, self._separator)
        result = True

        while True:
            try:
                command, modifiers, count = next(commands)
            except UnknownModifiersError as e:
                self.err('Unknown modifiers: %s' % ', '.join(e.args))
                return False
            except IncompatibleModifiersError as e:
                self.err('Incompatible modifiers: %s' % e.args[0])
                return False
            except StopIteration:
                break
            else:
                if not self._executeOneCommand(command, modifiers, count):
                    result = False

        return result

    def _executeOneCommand(self, command, modifiers, count):
        """
        Execute one command.

        @param command: A C{str} command to run.
        @param modifiers: A C{Modifiers} instance.
        @param count: An C{int} count, or C{None} if no count was given.
        @return: A C{bool} indicating if the command ran without error.
        """
        if modifiers.split:
            if not self._splitLines:
                self.debug('Line splitting switched ON')
            self._splitLines = True
        elif modifiers.noSplit:
            if self._splitLines:
                self.debug('Line splitting switched OFF')
            self._splitLines = False

        if modifiers.all:
            stackLen = len(self)
            if count is not None and count != stackLen:
                self.err(
                    '* modifier conflicts with explicit count %d '
                    '(stack has %d item%s)' %
                    (count, stackLen, '' if stackLen == 1 else 's'))
                return False

        if not command:
            self.debug('Empty command')
            return True

        done = self._tryFunction(command, modifiers, count)

        if done is False:
            done = self._tryVariable(command, modifiers)

        if done is False:
            done = self._trySpecial(command, modifiers, count)

        if done is False:
            done = self._tryEval(command, modifiers, count)

        if done is False and count is not None:
            self.err('Modifier count %d will not be used' % count)

        if done is False:
            done = self._tryExec(command)

        if done is False:
            return False

        return True

    def _tryFunction(self, command, modifiers, count):
        if modifiers.forceCommand:
            return False

        try:
            function = self._functions[command]
        except KeyError:
            self.debug('%s is not a known function' % (command,))
            return False

        self.debug('Found function %r' % command)

        if modifiers.push:
            self._finalize(function.func, modifiers)
            return

        if count is None:
            nArgs = len(self) if modifiers.all else function.nArgs
        else:
            nArgs = count

        if len(self) < nArgs:
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

            self.debug('Calling %s with %r' % (function.name, tuple(args)))
            try:
                result = function.func(*args)
            except BaseException as e:
                self.err('Exception running %s(%s): %s' %
                         (function.name, ', '.join(map(str, args)), e))
            else:
                self._finalize(result, modifiers, nPop=nArgs)

    def _tryVariable(self, command, modifiers):
        if modifiers.forceCommand:
            return False

        if command in self._variables:
            self._finalize(
                Variable(command, self._variables) if modifiers.push
                else self._variables[command], modifiers)
        else:
            return False

    def _trySpecial(self, command, modifiers, count):
        if command in self._special:
            try:
                self._special[command](self, modifiers, count)
            except EOFError:
                raise
            except BaseException as e:
                self.err('Could not run special command %r: %s' % (command, e))
        elif modifiers.forceCommand:
            self.err('Unknown command: %s' % command)
        else:
            return False

    def _tryEval(self, command, modifiers, count):
        try:
            value = eval(command, globals(), self._variables)
        except BaseException as e:
            self.debug('Could not eval(%r): %s' % (command, e))
            return False
        else:
            self.debug('eval %s worked: %r' % (command, value))
            count = 1 if count is None else count
            self._finalize(value, modifiers=modifiers, repeat=count)

    def _tryExec(self, command):
        try:
            exec(command, globals(), self._variables)
        except BaseException as e:
            self.err('Could not exec(%r): %s' % (command, e))
            return False
        else:
            self.debug('exec worked.')
