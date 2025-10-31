import builtins
import decimal
import functools
import inspect
import math
import operator
import sys
from pprint import pprint
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TextIO,
    Tuple,
    Union,
)

from engineering_notation import EngNumber
from rich.console import Console

from rpnpy.errors import (
    CalculatorError,
    IncompatibleModifiersError,
    StackError,
    UnknownModifiersError,
)
from rpnpy.functions import FUNCTIONS
from rpnpy.inspect import countArgs
from rpnpy.io import findCommands
from rpnpy.modifiers import Modifiers
from rpnpy.utils import plural


class Function:
    def __init__(
        self, moduleName: str, name: str, func: Callable, nArgs: Optional[int]
    ) -> None:
        self.moduleName = moduleName
        self.name = name
        self.func = func
        self.nArgs = nArgs

    def __call__(self, *args: Any, **kw: Any) -> Any:
        return self.func(*args, **kw)

    def __repr__(self) -> str:
        assert self.nArgs is not None
        return (
            f"Function({self.name} (calls {self.path} with {self.nArgs} "
            f"arg{plural(self.nArgs)}))"
        )

    @property
    def path(self) -> str:
        return f"{self.moduleName}.{self.name}"


class Variable:
    def __init__(self, name: str, variables: Dict[str, Any]) -> None:
        self.name = name
        self._variables = variables

    def __repr__(self) -> str:
        name = self.name
        return f"Variable({name}, current value: {self._variables[name]}!r)"


class Calculator:
    OVERRIDES = set("builtins.list builtins.map builtins.quit functools.reduce".split())
    # Sentinel value for calculator functions to return to indicate that they
    # did not result in a value that can/should be printed.
    NO_VALUE = object()

    def __init__(
        self,
        autoPrint: bool = False,
        splitLines: bool = True,
        separator: Optional[str] = None,
        outfp: TextIO = sys.stdout,
        errfp: TextIO = sys.stderr,
        debug: bool = False,
        color: bool = False,
    ) -> None:
        self._autoPrint = autoPrint
        self._splitLines = splitLines
        self._separator = separator
        self._outfp = outfp
        self._errfp = errfp
        self._debug = debug
        if color:
            self._console = Console()
            self._errorConsole = Console(stderr=True)
        else:
            self._console = self._errorConsole = None
        self.stack = []
        self._previousStack = self._previousVariables = None
        self._functions = {}
        self._special = {}
        self._variables = {
            "self": self,
        }

        self.addSpecialCases()
        self.addFunctions()
        self.addModules()
        self.addAbbrevs()
        self.addConstants()

    def __len__(self) -> int:
        return len(self.stack)

    def report(self, *args: Any, **kw: Any) -> None:
        if self._console:
            self._console.print(*args, style="bold green", **kw)
        else:
            print(*args, file=self._outfp, **kw)

    def err(self, *args: Any, **kw: Any) -> None:
        if self._errorConsole:
            self._errorConsole.print(*args, style="bold red", **kw)
        else:
            print(*args, file=self._errfp, **kw)

    def debug(self, *args: Any, **kw: Any) -> None:
        if self._debug:
            if self._console:
                self._console.print("      #", *args, style="bold yellow", **kw)
            else:
                print("      #", *args, file=self._errfp, **kw)

    def pprint(self, *args: Any, **kw: Any) -> None:
        if self._console:
            self._console.print(*args, **kw)
        else:
            pprint(*args, stream=self._outfp, **kw)

    def batch(self, fp: Iterable[str], finalPrint: bool = False) -> None:
        """Non-interactively read and execute commands from a file.

        @param fp: An iterator to read commands from.
        @param finalPrint: If C{True}, print the stack after all commands are
            run.
        """
        for line in fp:
            try:
                self.execute(line)
            except EOFError:
                break
        if finalPrint and self.stack:
            self.printStack(-1 if len(self) == 1 else None)

    def repl(self, prompt: str) -> None:
        """Interactive read-eval-print loop.

        @param prompt: The C{str} prompt to print at the start of each line.
        """
        while True:
            try:
                try:
                    line = input(prompt)
                except ValueError as e:
                    if str(e) == "I/O operation on closed file.":
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

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        nArgs: Optional[int] = None,
        moduleName: Optional[str] = None,
    ) -> None:
        name = name or func.__name__
        if name in self._functions:
            self.debug(
                "Registering new functionality for already known "
                "function named %r." % name
            )

        moduleName = moduleName or "calculator-registered-method"
        nArgs = countArgs(func, 1) if nArgs is None else nArgs
        self._functions[name] = Function(moduleName, name, func, nArgs)

    def addAbbrevs(self) -> None:
        for longName, shortNames in (
            ("math.log", ("log",)),
            ("math.sqrt", ("v",)),
            ("operator.attrgetter", ("attrgetter",)),
            ("operator.itemgetter", ("itemgetter",)),
            ("operator.methodcaller", ("methodcaller",)),
            ("operator.add", ("+",)),
            ("operator.eq", ("==",)),
            ("operator.mul", ("*",)),
            ("operator.ne", ("!=",)),
            ("operator.sub", ("-",)),
            ("operator.truediv", ("/", "div")),
            ("builtins.bool", ("bool",)),
            ("builtins.int", ("int",)),
            ("builtins.max", ("max",)),
            ("builtins.min", ("min",)),
            ("builtins.print", ("print",)),
            ("builtins.range", ("range",)),
            ("builtins.str", ("str",)),
        ):
            try:
                function = self._functions[longName]
            except KeyError:
                self.err("Long function name %r is unknown" % longName)
            else:
                for shortName in shortNames:
                    if shortName not in self._functions:
                        # self.err('Long name %r alias %r' %
                        # (longName, shortName))
                        self._functions[shortName] = function
                    else:
                        assert self._functions[shortName] is function

    def addFunctions(self) -> None:
        """
        Add the functions from functions.py
        """
        for func in FUNCTIONS:
            for name in func.names:
                self.debug("Adding special command %r for %s" % (name, func))
                self._special[name] = func

    def addModules(self) -> None:
        """
        Add callable functions from various modules.
        """
        for module in math, operator, builtins, functools, decimal:
            self.importCallables(module)

    def addSpecialCases(self) -> None:
        """
        Add argument counts for functions that cannot have their signatures
        inspected.
        """
        for module, func, nArgs in (
            (math, math.log, 1),
            (builtins, builtins.bool, 1),
            (builtins, builtins.int, 1),
            (builtins, builtins.float, 1),
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
            longName = "%s.%s" % (module.__name__, func.__name__)
            try:
                self._functions[longName]
            except KeyError:
                self._functions[longName] = Function(
                    module.__name__, func.__name__, func, nArgs
                )
            else:
                self.err("Long function name %r is already set" % longName)

    def addConstants(self) -> None:
        """Add some constants (well, constant in theory) from math"""
        constants = [
            ("e", math.e),
            ("inf", math.inf),
            ("nan", math.nan),
            ("pi", math.pi),
            ("tau", math.tau),
        ]

        for name, value in constants:
            if name in self._variables:
                self.err("%r is already a variable!" % name)
            else:
                self._variables[name] = value

    def importCallables(self, module: Any) -> None:
        moduleName = module.__name__
        exec("import " + moduleName, globals(), self._variables)
        callables = inspect.getmembers(module, callable)

        for name, func in callables:
            if name.startswith("_"):
                continue

            try:
                if issubclass(func, BaseException):
                    continue
            except TypeError:
                pass

            nArgs = countArgs(func)

            if nArgs is None:
                continue

            path = f"{moduleName}.{name}"

            if path in self.OVERRIDES:
                self.debug(f"Not importing {path!r}")
                continue

            if path not in self._functions:
                # Add the function to our functions dict along with a
                # default number of positional parameters it expects. This
                # allows the user to call it and have the arguments taken
                # from the stack (the number of arguments used can always
                # be specified on the command line (e.g., :3)).
                exec(
                    'self._functions["%s"] = Function("%s", "%s", %s, %d)'
                    % (path, moduleName, name, path, nArgs)
                )

            # Import the function by name to allow the user to use it in a
            # command with an explicit argument, instead of applying it to
            # whatever is on the stack.
            if name in self._variables:
                self.debug(f"name {name} already defined! Ignoring {path}")
            else:
                exec(f"from {moduleName} import {name}", globals(), self._variables)
                if name not in self._variables:
                    self.err(f"name {name!r} not now defined!!!")
                assert name not in self._functions
                self._functions[name] = self._functions[path]

    def printStack(self, n: Optional[Union[int, slice]] = None) -> None:
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
                if n == -1:
                    self.err("Cannot print top of stack item (stack is empty).")
                else:
                    self.err(
                        f"Cannot print stack item {n} (stack has only {len(self)} "
                        f"item{plural(len(self))})."
                    )

    def saveState(self) -> None:
        """Save the stack and variable state."""
        self._previousStack = self.stack.copy()
        self._previousVariables = self._variables.copy()

    def _finalize(
        self,
        result: Any,
        modifiers: Modifiers,
        nPop: int = 0,
        extend: bool = False,
        repeat: int = 1,
        noValue: bool = False,
    ) -> None:
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
                result = list(iterator)

        if not (modifiers.preserveStack or noValue):
            add = self.stack.extend if extend else self.stack.append
            for _ in range(repeat):
                add(result)

    def execute(self, line: str) -> bool:
        """
        Execute a line of commands. Stop executing commands on any error.

        @param line: A C{str} command line to run.
        @return: A C{bool} indicating if all commands ran without error.
        """
        commands = findCommands(line, self._splitLines, self._separator)

        while True:
            try:
                command, modifiers, count = next(commands)
            except UnknownModifiersError as e:
                self.err("Unknown modifiers: %s" % ", ".join(e.args))
                return False
            except IncompatibleModifiersError as e:
                self.err(f"Incompatible modifiers: {e.args[0]}")
                return False
            except CalculatorError as e:
                self.err(f"Incompatible modifiers: {e.args[0]}")
                return False
            except StopIteration:
                break
            else:
                if not self._executeOneCommand(command, modifiers, count):
                    # Print a debug message if there were pending commands
                    # that did not get run at all.
                    try:
                        command, modifiers, count = next(commands)
                    except StopIteration:
                        pass
                    else:
                        self.debug(
                            f"Ignoring commands from {command!r} on due to "
                            "previous error."
                        )
                    return False

        return True

    def _executeOneCommand(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> bool:
        """
        Execute one command.

        @param command: A C{str} command to run.
        @param modifiers: A C{Modifiers} instance.
        @param count: An C{int} count, or C{None} if no count was given.
        @return: A C{bool} indicating if the command ran without error.
        """
        if modifiers.split:
            if not self._splitLines:
                self.debug("Line splitting switched ON")
            self._splitLines = True
        elif modifiers.noSplit:
            if self._splitLines:
                self.debug("Line splitting switched OFF")
            self._splitLines = False

        if modifiers.all:
            stackLen = len(self)
            if count is not None and count != stackLen:
                self.err(
                    f"* modifier conflicts with explicit count {count} "
                    f"(stack has {stackLen} item{plural(stackLen)})"
                )
                return False

        if modifiers.autoPrint:
            self.toggleAutoPrint()

        if modifiers.debug:
            self.toggleDebug()

        if not command:
            self.debug("Empty command")
            return True

        if count == 0:
            self.debug("Count was zero - nothing to do!")
            return True

        try:
            for func in (
                self._tryFunction,
                self._tryVariable,
                self._trySpecial,
                self._tryEvalExec,
            ):
                status, value = func(command, modifiers, count)
                if status:
                    if value is not self.NO_VALUE and (
                        modifiers.print or self._autoPrint
                    ):
                        self.pprint(value)
                    return True
            else:
                raise CalculatorError(f"Could not find a way to execute {command!r}.")
        except (CalculatorError, StackError) as e:
            for err in e.args:
                self.err(err)
            return False

    def _tryFunction(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[bool, Any]:
        if modifiers.forceCommand:
            return False, self.NO_VALUE

        try:
            function = self._functions[command]
        except KeyError:
            self.debug(f"{command!r} is not a known function.")
            return False, self.NO_VALUE

        self.debug(f"Found function {command!r}.")

        if modifiers.push:
            self._finalize(function.func, modifiers)
            return True, function.func

        return self._runFunction(command, modifiers, count, function)

    def _runFunction(
        self,
        command: str,
        modifiers: Modifiers,
        count: Optional[int],
        function: Function,
    ) -> Tuple[bool, Any]:
        "Run a Python function."

        nArgs = (
            (len(self) if modifiers.all else function.nArgs) if count is None else count
        )

        assert nArgs is not None

        if len(self) < nArgs:
            raise CalculatorError(
                "Not enough args on stack! (%s needs %d arg%s, stack has "
                "%d item%s)"
                % (command, nArgs, plural(nArgs), len(self), plural(len(self)))
            )

        args = self.convertStackArgs(self.stack[-nArgs:]) if nArgs else []

        if modifiers.reverse and args:
            # Reverse the order of args so that the top of the stack (last
            # element of the stack list) becomes the first argument to the
            # function instead of the last.
            args = args[::-1]

        self.debug(f"Calling {function.name!r} with {tuple(args)!r}")
        try:
            result = function.func(*args)
        except BaseException as e:
            raise CalculatorError(
                "Exception running %s(%s): %s"
                % (function.name, ", ".join(map(str, args)), e)
            ) from e
        else:
            self._finalize(result, modifiers, nPop=nArgs)
            return True, result

    def _tryVariable(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[bool, Any]:
        if modifiers.forceCommand:
            return False, self.NO_VALUE

        if command in self._variables:
            self.debug(
                f"{command!r} is a variable (value {self._variables[command]!r})"
            )
            value = self._variables[command]
            if callable(value):
                if not modifiers.push:
                    return self._runFunction(
                        command,
                        modifiers,
                        count,
                        Function("<stdin>", value.__name__, value, countArgs(value, 1)),
                    )
            else:
                if modifiers.push:
                    value = Variable(command, self._variables)
            if count is None:
                count = 1
            self._finalize([value] * count, modifiers, extend=True)
            return True, value
        else:
            self.debug(f"{command!r} is not a variable")
            return False, self.NO_VALUE

    def _trySpecial(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[bool, Any]:
        if command in self._special:
            try:
                value = self._special[command](self, modifiers, count)
            except EOFError:
                raise
            except BaseException as e:
                raise CalculatorError(
                    f"Could not run special command {command!r}: {e}"
                ) from e
            return True, value

        if modifiers.forceCommand:
            raise CalculatorError(f"Unknown special command: {command!r}.")

        return False, self.NO_VALUE

    def _tryEvalExec(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[bool, Any]:
        errors = []
        possibleWhiteSpace = False
        try:
            value = eval(command, globals(), self._variables)
        except BaseException as e:
            err = str(e)
            errors.append(f"Could not eval({command!r}): {err}")
            if self._splitLines and err.startswith(
                "unexpected EOF while parsing (<string>, line 1)"
            ):
                possibleWhiteSpace = True

            try:
                value = EngNumber(command)
            except decimal.InvalidOperation:
                try:
                    exec(command, globals(), self._variables)
                except BaseException as e:
                    err = str(e)
                    errors.append(f"Could not exec({command!r}): {err}")
                    if (
                        not possibleWhiteSpace
                        and self._splitLines
                        and err.startswith(
                            "unexpected EOF while parsing (<string>, line 1)"
                        )
                    ):
                        possibleWhiteSpace = True

                    if possibleWhiteSpace:
                        errors.append(
                            "Did you accidentally include whitespace in a command line?"
                        )
                    raise CalculatorError(*errors) from e
                else:
                    self.debug(f"exec({command!r}) worked.")
                    return True, self.NO_VALUE
            else:
                self.debug(f"EngNumber({command}) worked: {value!r}")
                count = 1 if count is None else count
                self._finalize(value, modifiers=modifiers, repeat=count)
                return True, value
        else:
            self.debug(f"eval {command!r} worked: {value!r}")
            count = 1 if count is None else count
            self._finalize(value, modifiers=modifiers, repeat=count)
            return True, value

    def convertStackArgs(self, args: Iterable[Any]) -> List[Any]:
        """Convert stack items to arguments for functions.

        @param args: An iterable of stack items.
        @return: A C{list} of arguments taken from the stack items.
        """
        result = []
        for arg in args:
            if isinstance(arg, Function):
                result.append(arg.func)
            elif isinstance(arg, Variable):
                result.append(self._variables[arg.name])
            else:
                result.append(arg)

        return result

    def toggleAutoPrint(self, newValue: Optional[bool] = None) -> None:
        """Turn auto printing on/off.

        @param newValue: A C{bool} new setting or C{None} to toggle.
        """
        if newValue is None:
            if self._autoPrint:
                self.debug("Auto print off")
                self._autoPrint = False
            else:
                self._autoPrint = True
                self.debug("Auto print on")
        else:
            if newValue:
                self._autoPrint = True
                self.debug("Auto print on")
            else:
                self.debug("Auto print off")
                self._autoPrint = False

    def toggleDebug(self, newValue: Optional[bool] = None) -> None:
        """Turn debug on/off.

        @param newValue: A C{bool} new setting or C{None} to toggle.
        """
        if newValue is None:
            if self._debug:
                self.debug("Debug off")
                self._debug = False
            else:
                self._debug = True
                self.debug("Debug on")
        else:
            if newValue:
                self._debug = True
                self.debug("Debug on")
            else:
                self.debug("Debug off")
                self._debug = False

    def _findWithArgs(
        self,
        command: str,
        description: str,
        predicate: Callable[[Any], bool],
        defaultArgCount: Callable[[Any], int],
        modifiers: Modifiers,
        count: Optional[int],
    ) -> Tuple[Any, Tuple[Any, ...]]:
        """
        Look for something (e.g., a callable function or a string) and its
        arguments on the stack.

        @param command: The C{str} name of the command that was invoked.
        @param description: A C{str} describing what is being sought. Used in
            error messages if no suitable stack item is found.
        @param predicate: A one-arg C{callable} that will be passed stack
            items and must return C{True} when it identifies something that
            satisfies the need of the caller.
        @param defaultArgCount: A C{callable} that can be passed the found
            stack item and which reurns an C{int} indicating how many
            arguments should be associated with it.
        @param modifier: A C{Modifiers} instance.
        @param count: An C{int} count of the number of arguments wanted (or
            C{None} if no count was given).
        @raise StackError: If there is a problem.
        @return: A 2-C{tuple} of the found item (satisfying the predicate) and
            a C{tuple} of its arguments. If a suitable stack item cannot be
            found, return (None, None).
        """
        stackLen = len(self)

        if stackLen < 2 or count is not None and stackLen < count + 1:
            raise StackError(
                f"Cannot run {command!r} (stack has only {stackLen} "
                f"item{plural(stackLen)})."
            )

        if modifiers.reverse:
            item = self.stack[-1]

            if not predicate(item):
                raise StackError(f"Top stack item ({item!r}) is not {description}.")

            if count is None:
                count = stackLen - 1 if modifiers.all else defaultArgCount(item)

            nargsAvail = stackLen - 1
            if nargsAvail < count:
                raise StackError(
                    f"Cannot run {command!r} with {count} argument{plural(count)} "
                    f"(stack has only {nargsAvail} item{plural(nargsAvail)} available)."
                )

            args = self.stack[-(count + 1) : -1]
        else:
            if count is None:
                if modifiers.all:
                    item = self.stack[0]
                    args = self.stack[1:]
                else:
                    args = []
                    for arg in reversed(self.stack):
                        if predicate(arg):
                            break
                        else:
                            args.append(arg)
                    else:
                        raise StackError(f"Could not find {description} item on stack.")

                    item = self.stack[-(len(args) + 1)]
                    args = args[::-1]
            else:
                item = self.stack[-(count + 1)]

                if not predicate(item):
                    raise StackError(
                        f"Cannot run {command!r} with {count} argument{plural(count)}. "
                        f"Stack item ({item!r}) is not {description}."
                    )

                args = self.stack[-count:]

        return item, self.convertStackArgs(args)

    def findCallableAndArgs(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[Callable, Tuple[Any, ...]]:
        """Look for a callable function and its arguments on the stack.

        @param modifier: A C{Modifiers} instance.
        @return: A 2-C{tuple} of the function and a C{tuple} of its arguments.
        """

        def defaultArgCount(func: Callable) -> int:
            return countArgs(func, 1)

        return self._findWithArgs(
            command, "callable", callable, defaultArgCount, modifiers, count
        )

    def findStringAndArgs(
        self, command: str, modifiers: Modifiers, count: Optional[int]
    ) -> Tuple[str, Tuple[Any, ...]]:
        """Look for a string its arguments on the stack.

        @param modifier: A C{Modifiers} instance.
        @return: A 2-C{tuple} of the string and a C{tuple} of its arguments.
        """

        def predicate(x: Any) -> bool:
            return isinstance(x, str)

        def defaultArgCount(x: Any) -> int:
            return 1

        return self._findWithArgs(
            command, "a string", predicate, defaultArgCount, modifiers, count
        )

    def setVariable(self, variable: str, value: Any) -> None:
        """
        Set the value of a variable.

        @param variable: The C{str} variable name.
        @param value: The value to give the variable.
        """
        self._variables[variable] = value
