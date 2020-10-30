import sys
from unittest import TestCase
from io import StringIO
from decimal import Decimal
import math
import operator
from engineering_notation import EngNumber

from rpnpy import Calculator
from rpnpy.errors import StackError
from rpnpy.modifiers import Modifiers, strToModifiers


class TestDebug(TestCase):
    "Test setting/toggling debug output"

    def testDebugOffByDefault(self):
        "debugging must be off by default"
        c = Calculator()
        self.assertFalse(c._debug)

    def testStartWithDebugOn(self):
        "debugging must be settable via __init__"
        c = Calculator(debug=True)
        self.assertTrue(c._debug)

    def testDebugOn(self):
        "It must be possible to turn debugging on"
        c = Calculator()
        c.toggleDebug(True)
        self.assertTrue(c._debug)

    def testDebugOff(self):
        "It must be possible to turn debugging off"
        c = Calculator()
        c.toggleDebug(False)
        self.assertFalse(c._debug)

    def testToggleDebugOn(self):
        "It must be possible to toggle debugging on"
        c = Calculator()
        # Double-check it starts out off (don't rely on above test).
        self.assertFalse(c._debug)
        c.toggleDebug()
        self.assertTrue(c._debug)

    def testToggleDebugOff(self):
        "It must be possible to toggle debugging on"
        c = Calculator()
        # Double-check it starts out off (don't rely on above test).
        c.toggleDebug()
        self.assertTrue(c._debug)
        c.toggleDebug()
        self.assertFalse(c._debug)

    def testDebugOnViaModifier(self):
        "It must be possible to turn debugging on using a modifier"
        c = Calculator()
        c.execute(':D')
        self.assertTrue(c._debug)

    def testDebugOffViaModifier(self):
        "It must be possible to turn debugging off using a modifier"
        c = Calculator(debug=True)
        c.execute(':D')
        self.assertFalse(c._debug)


class TestCalculator(TestCase):

    def testEmptyStack(self):
        "A calculator must start life with an empty stack"
        self.assertEqual([], Calculator().stack)

    def testPushNumber(self):
        "Pushing a number must work as expected"
        c = Calculator()
        c.execute('4')
        (result,) = c.stack
        self.assertEqual(4, result)

    def testPushString(self):
        "Pushing a string must work as expected"
        c = Calculator()
        c.execute("'4'")
        (result,) = c.stack
        self.assertEqual('4', result)

    def testPushAbs(self):
        "Pushing the operator.abs function must work as expected"
        c = Calculator()
        c.execute('operator.abs :!')
        (result,) = c.stack
        self.assertIs(operator.abs, result)

    def testAdd(self):
        "Adding must work"
        c = Calculator()
        c.execute('3 4 +')
        (result,) = c.stack
        self.assertEqual(7, result)

    def testAddOneArg(self):
        "Adding must give an error if there is only one thing on the stack"
        err = StringIO()
        c = Calculator(errfp=err)
        c.execute('3 +')
        self.assertEqual(
            'Not enough args on stack! (+ needs 2 args, stack has 1 item)\n',
            err.getvalue())

    def testAddVariables(self):
        "add must work correctly when Variable instances are on the stack"
        c = Calculator()
        c.execute('a=4 b=5')
        c.execute('a :!')
        c.execute('b :!')
        c.execute('+')
        (result,) = c.stack
        self.assertEqual(9, result)

    def testRegisterWithArgCount(self):
        """Registering and calling a new function and passing its argument
           count must work"""
        def double(n):
            return 2 * n

        c = Calculator()
        c.register(double, name='double', nArgs=1)
        c.execute('3 double')
        (result,) = c.stack
        self.assertEqual(6, result)

    def testRegisterWithArgCount2(self):
        """Registering and calling a new function and passing its argument
           count must work"""
        def doubleMax(*args):
            return 2 * max(*args)

        c = Calculator()
        c.register(doubleMax, name='doubleMax', nArgs=3)
        c.execute('3 5 6 7 doubleMax')
        (onStack, result) = c.stack
        self.assertEqual(14, result)
        self.assertEqual(3, onStack)

    def testRegisterWithoutArgCount(self):
        """Registering and calling a new function without passing its argument
           count must work"""
        def addAndDouble(i, j):
            return 2 * (i + j)

        c = Calculator()
        c.register(addAndDouble, name='addAndDouble')
        c.execute('3 5 addAndDouble')
        (result,) = c.stack
        self.assertEqual(16, result)

    def testRegisterCelciusNoExplicitName(self):
        """Register and call a function to convert Fahrenheit to Celcius but do
        not pass a function name"""
        def celcius(f):
            return (f - 32) / 1.8

        c = Calculator()
        c.register(celcius)
        c.execute('212 celcius')
        (result,) = c.stack
        self.assertEqual(100, result)

    def testRegisterLambdaWithExplicitName(self):
        "Register and call a function defined using lambda with a passed name"
        c = Calculator()
        c.register(lambda: 3, name='xx')
        c.execute('xx')
        (result,) = c.stack
        self.assertEqual(3, result)

    def testRegisterLambdaWithNoName(self):
        "Register and call a function defined using lambda and no passed name"
        c = Calculator()
        c.register(lambda: 3)
        # The function will be called '<lambda>', which is a bit dangerous
        # (could easily be accidentally be overwritten).
        c.execute('<lambda>')
        (result,) = c.stack
        self.assertEqual(3, result)

    def testDef(self):
        "Use def to make a new function."
        c = Calculator(splitLines=False)
        c.execute('def celcius(f): return (f - 32) / 1.8')
        c.execute('212')
        c.execute('celcius')
        (result,) = c.stack
        self.assertEqual(100, result)

    def testDefThenPush(self):
        "Use def to make a new function and push it onto the stack."
        c = Calculator(splitLines=False)
        c.execute('def celcius(f): return (f - 32) / 1.8')
        c.execute('celcius :!')
        (result,) = c.stack
        self.assertEqual('celcius', result.__name__)

    def testSumOneArg(self):
        "sum must take one arg by default"
        c = Calculator()
        self.assertEqual(1, c._functions['sum'].nArgs)

    def testPowTwoArgs(self):
        "pow must take two args by default"
        c = Calculator()
        self.assertEqual(2, c._functions['pow'].nArgs)

    def testSwap(self):
        "swap must work as expected"
        c = Calculator()
        c.execute('4 5')
        self.assertEqual([4, 5], c.stack)
        c.execute('swap')
        self.assertEqual([5, 4], c.stack)

    def testDup(self):
        "dup must work as expected"
        c = Calculator()
        c.execute('4 d')
        self.assertEqual([4, 4], c.stack)
        c.execute('dup')
        self.assertEqual([4, 4, 4], c.stack)

    def testIterateString(self):
        "The :i (iterate) modifier must work as expected on a string"
        c = Calculator()
        c.execute('"hello" :i')
        (result,) = c.stack
        self.assertEqual(['h', 'e', 'l', 'l', 'o'], result)

    def testItemgetter(self):
        "itemgetter must work correctly"
        c = Calculator(splitLines=False)
        c.execute('1')
        c.execute('itemgetter')
        c.execute('[[1, 2, 3], [4, 5, 6]]')
        c.execute('map :i')
        (result,) = c.stack
        self.assertEqual([2, 5], result)

    def testList(self):
        "Converting the top of the stack to a list must work"
        c = Calculator()
        c.execute('"hey" list')
        (result,) = c.stack
        self.assertEqual(['h', 'e', 'y'], result)

    def testList2(self):
        "Converting the top two items of the stack to a list must work"
        c = Calculator()
        c.execute('4 5 list:2')
        c.printStack()
        (result,) = c.stack
        self.assertEqual([4, 5], result)

    def testListAll(self):
        "Converting all items of the stack to a list must work"
        c = Calculator()
        c.execute('4 5 6 list:*')
        c.printStack()
        (result,) = c.stack
        self.assertEqual([4, 5, 6], result)

    def testPushList(self):
        "It must be possible to push list onto the stack"
        c = Calculator()
        c.execute('list :!')
        (result,) = c.stack
        self.assertIs(list, result)

    def testPushNone(self):
        "It must be possible to push None onto the stack"
        c = Calculator()
        c.execute('None')
        (result,) = c.stack
        self.assertIs(None, result)

    def testPushTrue(self):
        "It must be possible to push True onto the stack"
        c = Calculator()
        c.execute('True')
        (result,) = c.stack
        self.assertIs(True, result)

    def testPushFalse(self):
        "It must be possible to push False onto the stack"
        c = Calculator()
        c.execute('False')
        (result,) = c.stack
        self.assertIs(False, result)

    def testBatch(self):
        "It must be possible to read from a file using the batch method"
        infp = StringIO('3\n4\n+\np\n')
        outfp = StringIO()
        c = Calculator(outfp=outfp)
        c.batch(infp)
        self.assertEqual('7\n', outfp.getvalue())

    def testREPL(self):
        "It must be possible to read input in REPL form"
        infp = StringIO('3\n4\n+\np\n')
        outfp = StringIO()
        c = Calculator(outfp=outfp)
        stdin = sys.stdin
        sys.stdin = infp
        c.repl('prompt')
        sys.stdin = stdin
        self.assertEqual('7\n', outfp.getvalue())

    def testCountConflictsWithAllModifier(self):
        "If :* and a count is given, it's an error if they don't agree"
        errfp = StringIO()
        c = Calculator(errfp=errfp)
        self.assertFalse(c.execute('4 5 6 list:*5'))
        error = ('* modifier conflicts with explicit count 5 '
                 '(stack has 3 items)\n')
        self.assertEqual(error, errfp.getvalue())

    def testFloat(self):
        "It must be possible to convert something to a float"
        c = Calculator()
        c.execute('4 float')
        (result,) = c.stack
        self.assertEqual(4.0, result)


class TestReverseModifier(TestCase):
    "Test the reverse modifier"

    def testReverseSubtractionArgs(self):
        "Reverse the args in a subtraction"
        c = Calculator()
        c.execute('5 4 -:r')
        (result,) = c.stack
        self.assertEqual(-1, result)

    def testMap(self):
        "Call map with args reversed from their normal order"
        c = Calculator()
        c.execute('[1,2,3]')
        c.execute('str :!')
        c.execute('map :ir')
        (result,) = c.stack
        self.assertEqual(['1', '2', '3'], result)


class TestReverseSpecialCommand(TestCase):
    "Test the reverse special command"

    def testReverse1(self):
        "Reversing just the top element of the stack does nothing"
        c = Calculator()
        c.execute('4 5 reverse:1')
        self.assertEqual([4, 5], c.stack)

    def testReverse(self):
        "Reverse (by default) the top two elements of the stack"
        c = Calculator()
        c.execute('4 5 reverse')
        self.assertEqual([5, 4], c.stack)

    def testReverseAll(self):
        "It must be possible to reverse all the stack"
        c = Calculator()
        c.execute('4 6 5 reverse:*')
        self.assertEqual([5, 6, 4], c.stack)

    def testReverseWithStackTooSmall(self):
        "It's an error if an attempt is made to reverse too many things"
        errfp = StringIO()
        c = Calculator(errfp=errfp)
        self.assertFalse(c.execute('4 5 6 reverse:10'))
        error = ("Could not run special command 'reverse': Cannot reverse 10 "
                 "items (stack length is 3)\n")
        self.assertEqual(error, errfp.getvalue())


class TestDecimal(TestCase):
    "Test working with Decimal instances"

    def testPush(self):
        "It must be possible to push Decimal by itself"
        c = Calculator()
        c.execute('Decimal :!')
        (result,) = c.stack
        self.assertIs(Decimal, result)

    def testPushValue(self):
        "It must be possible to push a Decimal value"
        c = Calculator()
        c.execute('Decimal(4)')
        (result,) = c.stack
        self.assertEqual(Decimal(4), result)

    def testArithmetic(self):
        "It must be possible to operate on Decimals"
        c = Calculator()
        c.execute('Decimal(4) Decimal(6) +')
        (result,) = c.stack
        self.assertEqual(Decimal(10), result)
        c.execute('int')
        (result,) = c.stack
        self.assertEqual(10, result)


class TestJoin(TestCase):
    "Test the join special function"

    def testEmptyString(self):
        "Joining on an empty string must work"
        c = Calculator()
        c.execute('"" ["4","5","6"] join')
        (result,) = c.stack
        self.assertEqual('456', result)

    def testNonEmptyString(self):
        "Joining on a non-empty string must work"
        c = Calculator()
        c.execute('"-" ["4","5","6"] join')
        (result,) = c.stack
        self.assertEqual('4-5-6', result)

    def testNonStrings(self):
        "Joining things that are not string must work"
        c = Calculator()
        c.execute('"-" [4,5,6] join')
        (result,) = c.stack
        self.assertEqual('4-5-6', result)

    def testWithCount(self):
        "Joining several stack items must work"
        c = Calculator()
        c.execute('3 "-" 4 5 6 join:3')
        self.assertEqual([3, '4-5-6'], c.stack)

    def testAllStack(self):
        "Joining the whole stack"
        c = Calculator()
        c.execute('"-" 3 4 5 6 join:*')
        (result,) = c.stack
        self.assertEqual('3-4-5-6', result)

    def testEmptyStringReversed(self):
        "Joining on an empty string must work"
        c = Calculator()
        c.execute('["4","5","6"] "" join:r')
        (result,) = c.stack
        self.assertEqual('456', result)

    def testNonEmptyStringReversed(self):
        "Joining on a non-empty string must work"
        c = Calculator()
        c.execute('["4","5","6"] "-" join:r')
        (result,) = c.stack
        self.assertEqual('4-5-6', result)

    def testNonStringsReversed(self):
        "Joining things that are not string must work"
        c = Calculator()
        c.execute('[4,5,6] "-" join:r')
        (result,) = c.stack
        self.assertEqual('4-5-6', result)

    def testWithCountReversed(self):
        "Joining several stack items must work"
        c = Calculator()
        c.execute('3 4 5 6 "-" join:3r')
        self.assertEqual([3, '4-5-6'], c.stack)

    def testAllStackReversed(self):
        "Joining the whole stack"
        c = Calculator()
        c.execute('3 4 5 6 "-" join:*r')
        (result,) = c.stack
        self.assertEqual('3-4-5-6', result)


class TestFindCallableAndArgs(TestCase):
    "Test the findCallableAndArgs function"

    def testEmptyStack(self):
        "Calling on an empty stack must return None, None"
        c = Calculator()

        error = r"^Cannot run 'cmd' \(stack has only 0 items\)$"
        self.assertRaisesRegex(StackError, error, c.findCallableAndArgs,
                               'cmd', Modifiers(), None)

    def testStackLengthOne(self):
        "Calling on a stack with only one item must return None, None"
        errfp = StringIO()
        c = Calculator(errfp=errfp)
        c.execute('4')
        error = r"^Cannot run 'cmd' \(stack has only 1 item\)$"
        self.assertRaisesRegex(StackError, error, c.findCallableAndArgs,
                               'cmd', Modifiers(), None)

    def testStackLengthTwoNoCount(self):
        """Calling on a stack with two items and no count must return
        correctly. The number of stack items is obtained from the function
        signature"""
        c = Calculator()
        c.execute('log10 :!')
        c.execute('4')
        func, args = c.findCallableAndArgs('cmd', Modifiers(), None)
        self.assertIs(math.log10, func)
        self.assertEqual([4], args)

    def testStackLengthTwoWithCount(self):
        """Calling on a stack with two items and a count must return
        correctly."""
        c = Calculator()
        c.execute('log10 :!')
        c.execute('4')
        func, args = c.findCallableAndArgs('cmd', Modifiers(), 1)
        self.assertIs(math.log10, func)
        self.assertEqual([4], args)

    def testStackLengthThreeWithCountError(self):
        """Calling on a stack with three items and a count that points to a
        non-callable must result in an error"""
        errfp = StringIO()
        c = Calculator(errfp=errfp)
        c.execute('log10 :!')
        c.execute('4')
        c.execute('5')
        error = (r"^Cannot run 'cmd' with 1 argument. Stack item \(4\) is "
                 r"not callable$")
        self.assertRaisesRegex(StackError, error, c.findCallableAndArgs,
                               'cmd', Modifiers(), 1)

    def testStackLengthThree(self):
        "Calling on a stack with three items (count=2) must return correctly"
        c = Calculator()
        c.execute('log10 :!')
        c.execute('4')
        c.execute('5')
        func, args = c.findCallableAndArgs('cmd', Modifiers(), 2)
        self.assertIs(math.log10, func)
        self.assertEqual([4, 5], args)

    def testAllStack(self):
        "Calling on all the stack must return correctly"
        c = Calculator()
        c.execute('log10 :!')
        c.execute('4')
        c.execute('5')
        c.execute('6')
        func, args = c.findCallableAndArgs('cmd', strToModifiers('*'), None)
        self.assertIs(math.log10, func)
        self.assertEqual([4, 5, 6], args)


class TestFindCallableAndArgsReversed(TestCase):
    "Test the findCallableAndArgs function when the reversed modifier is used"

    def testEmptyStack(self):
        "Calling on an empty stack must return None, None"
        c = Calculator()
        error = r"Cannot run 'cmd' \(stack has only 0 items\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', strToModifiers('r'), None)

    def testStackLengthOne(self):
        "Calling on a stack with only one item must return None, None"
        c = Calculator()
        c.execute('4')
        error = r"Cannot run 'cmd' \(stack has only 1 item\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', strToModifiers('r'), None)

    def testStackLengthTwoNoCount(self):
        """Calling on a stack with two items and no count must return
        correctly. The number of stack items is obtained from the function
        signature"""
        c = Calculator()
        c.execute('4')
        c.execute('log10 :!')
        func, args = c.findCallableAndArgs('cmd', strToModifiers('r'), None)
        self.assertIs(math.log10, func)
        self.assertEqual([4], args)

    def testStackLengthTwoWithCount(self):
        """Calling on a stack with two items and a count must return
        correctly."""
        c = Calculator()
        c.execute('4')
        c.execute('log10 :!')
        func, args = c.findCallableAndArgs('cmd', strToModifiers('r'), 1)
        self.assertIs(math.log10, func)
        self.assertEqual([4], args)

    def testStackLengthThree(self):
        "Calling on a stack with three items (count=2) must return correctly"
        c = Calculator()
        c.execute('5')
        c.execute('4')
        c.execute('log10 :!')
        func, args = c.findCallableAndArgs('cmd', strToModifiers('r'), 2)
        self.assertIs(math.log10, func)
        self.assertEqual([5, 4], args)

    def testAllStack(self):
        "Calling on all the stack must return correctly"
        c = Calculator()
        c.execute('4')
        c.execute('5')
        c.execute('6')
        c.execute('log10 :!')
        func, args = c.findCallableAndArgs('cmd', strToModifiers('*r'), None)
        self.assertIs(math.log10, func)
        self.assertEqual([4, 5, 6], args)


class TestFindStringAndArgs(TestCase):
    "Test the findStringAndArgs function"

    def testEmptyStack(self):
        "Calling on an empty stack must return None, None"
        c = Calculator()
        error = r"^Cannot run 'cmd' \(stack has only 0 items\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', Modifiers(), None)

    def testStackLengthOne(self):
        "Calling on a stack with only one item must return None, None"
        c = Calculator()
        c.execute('4')
        error = r"^Cannot run 'cmd' \(stack has only 1 item\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', Modifiers(), None)

    def testStackLengthTwoNoCount(self):
        """Calling on a stack with two items and no count must return
        correctly. The number of stack items is obtained from the function
        signature"""
        c = Calculator()
        c.execute("'string'")
        c.execute('4')
        string, args = c.findStringAndArgs('cmd', Modifiers(), None)
        self.assertEqual('string', string)
        self.assertEqual([4], args)

    def testStackLengthTwoWithCount(self):
        """Calling on a stack with two items and a count must return
        correctly."""
        c = Calculator()
        c.execute("'string'")
        c.execute('4')
        string, args = c.findStringAndArgs('cmd', Modifiers(), 1)
        self.assertEqual('string', string)
        self.assertEqual([4], args)

    def testStackLengthThreeWithCountError(self):
        """Calling on a stack with three items and a count that points to a
        non-string must result in an error"""
        c = Calculator()
        c.execute("'string'")
        c.execute('4')
        c.execute('5')
        error = (r"^Cannot run 'cmd' with 1 argument. Stack item \(4\) is "
                 r"not a string$")
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', Modifiers(), 1)

    def testStackLengthThree(self):
        "Calling on a stack with three items (count=2) must return correctly"
        c = Calculator()
        c.execute("'string'")
        c.execute('4')
        c.execute('5')
        string, args = c.findStringAndArgs('cmd', Modifiers(), 2)
        self.assertEqual('string', string)
        self.assertEqual([4, 5], args)

    def testAllStack(self):
        "Calling on all the stack must return correctly"
        c = Calculator()
        c.execute("'string'")
        c.execute('4')
        c.execute('5')
        c.execute('6')
        string, args = c.findStringAndArgs('cmd', strToModifiers('*'), None)
        self.assertEqual('string', string)
        self.assertEqual([4, 5, 6], args)


class TestFindStringAndArgsReversed(TestCase):
    "Test the findStringAndArgs function when the reversed modifier is used"

    def testEmptyStack(self):
        "Calling on an empty stack must return None, None"
        c = Calculator()
        error = r"^Cannot run 'cmd' \(stack has only 0 items\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', strToModifiers('r'), None)

    def testStackLengthOne(self):
        "Calling on a stack with only one item must result in a StackError"
        c = Calculator()
        c.execute('4')
        error = r"^Cannot run 'cmd' \(stack has only 1 item\)$"
        self.assertRaisesRegex(StackError, error, c.findStringAndArgs,
                               'cmd', strToModifiers('r'), None)

    def testStackLengthTwoNoCount(self):
        """Calling on a stack with two items and no count must return
        correctly. The number of stack items is obtained from the function
        signature"""
        c = Calculator()
        c.execute('4')
        c.execute("'string'")
        string, args = c.findStringAndArgs('cmd', strToModifiers('r'), None)
        self.assertEqual('string', string)
        self.assertEqual([4], args)

    def testStackLengthTwoWithCount(self):
        """Calling on a stack with two items and a count must return
        correctly."""
        c = Calculator()
        c.execute('4')
        c.execute("'string'")
        string, args = c.findStringAndArgs('cmd', strToModifiers('r'), 1)
        self.assertEqual('string', string)
        self.assertEqual([4], args)

    def testStackLengthThree(self):
        "Calling on a stack with three items (count=2) must return correctly"
        c = Calculator()
        c.execute('5')
        c.execute('4')
        c.execute("'string'")
        string, args = c.findStringAndArgs('cmd', strToModifiers('r'), 2)
        self.assertEqual('string', string)
        self.assertEqual([5, 4], args)

    def testAllStack(self):
        "Calling on all the stack must return correctly"
        c = Calculator()
        c.execute('4')
        c.execute('5')
        c.execute('6')
        c.execute("'string'")
        string, args = c.findStringAndArgs('cmd', strToModifiers('*r'), None)
        self.assertEqual('string', string)
        self.assertEqual([4, 5, 6], args)


class TestApply(TestCase):
    "Test the apply special function"

    def testApplyNoCount(self):
        "apply must work correctly when not given a count"
        c = Calculator()
        c.execute('abs :!')
        c.execute('-1')
        c.execute('apply')
        (result,) = c.stack
        self.assertEqual(1, result)

    def testApplyWithCount(self):
        "apply must work correctly when given a count"
        c = Calculator()
        c.execute('+ :!')
        c.execute('3 5')
        c.execute('apply :2')
        (result,) = c.stack
        self.assertEqual(8, result)

    def testApplyVariables(self):
        "apply must work correctly when Variable instances are on the stack"
        c = Calculator()
        c.execute('a=4 b=5')
        c.execute('+ :!')
        c.execute('a :!')
        c.execute('b :!')
        c.execute('apply')
        (result,) = c.stack
        self.assertEqual(9, result)


class TestReduce(TestCase):
    "Test the reduce special function"

    def testReduceAl(self):
        "Reduce must work correctly when told to operate on the whole stack"
        c = Calculator()
        c.execute('+ :!')
        c.execute('5')
        c.execute('6')
        c.execute('7')
        c.execute('reduce :*')
        (result,) = c.stack
        self.assertEqual(18, result)

    def testReduceWithCount(self):
        "Reduce must work correctly when given a count"
        c = Calculator()
        c.execute('+ :!')
        c.execute('5')
        c.execute('6')
        c.execute('reduce :2')
        (result,) = c.stack
        self.assertEqual(11, result)


class TestReduceReversed(TestCase):
    "Test the reduce special function when the reverse modifier is used"

    def testReduceAl(self):
        "Reduce must work correctly when told to operate on the whole stack"
        c = Calculator()
        c.execute('5')
        c.execute('6')
        c.execute('7')
        c.execute('+ :!')
        c.execute('reduce :*r')
        (result,) = c.stack
        self.assertEqual(18, result)

    def testReduceWithCount(self):
        "Reduce must work correctly when given a count"
        c = Calculator()
        c.execute('4')
        c.execute('5')
        c.execute('6')
        c.execute('+ :!')
        c.execute('reduce :2r')
        self.assertEqual([4, 11], c.stack)


class TestPop(TestCase):
    "Test the pop special function"

    def testPop(self):
        "Calling pop must work as expected"
        c = Calculator()
        c.execute('4 5 pop')
        (result,) = c.stack
        self.assertEqual(4, result)

    def testPop2(self):
        "Calling pop with a count of 2 must work as expected"
        c = Calculator()
        c.execute('3 4 5 pop:2')
        (result,) = c.stack
        self.assertEqual(3, result)

    def testPopAll(self):
        "Calling pop on the whole stack must work as expected"
        c = Calculator()
        c.execute('3 4 5 pop:*')
        self.assertEqual([], c.stack)

    def testPopWhenAVariableCalledPopExists(self):
        """pop must put a value on the stack when there is a varible of that
        name"""
        c = Calculator()
        c.execute('pop=4')
        c.execute('6')
        c.execute('5')
        c.execute('pop')
        self.assertEqual([6, 5, 4], c.stack)

    def testPopForcedCommandWhenAVariableCalledPopExists(self):
        """pop must work as expected when there is a varible of that name if
        we force the command to be run using :c"""
        c = Calculator()
        c.execute('pop=4')
        c.execute('6')
        c.execute('5')
        c.execute('pop:c')
        print(c.stack)
        (result,) = c.stack
        self.assertEqual(6, result)


class TestMap(TestCase):
    "Test the map special function"

    def testWithCount(self):
        "map must work as expected when given a count"
        c = Calculator()
        c.execute('str :!')
        c.execute('1 2 3')
        c.execute('map :3i')
        self.assertEqual(['1', '2', '3'], c.stack)

    def testIterateGenerator(self):
        "The :i (iterate) modifier must work as expected on a map generator"
        c = Calculator()
        c.execute('str :!')
        c.execute('[1,2,3]')
        c.execute('map :i')
        (result,) = c.stack
        self.assertEqual(['1', '2', '3'], result)

class TestEngineeringNotation(TestCase):
    "Test the engineering notation for values"

    def testInput(self):
        "A value suffixed by a unit should be recognized as engineering notation"
        c = Calculator()
        c.execute('2k')
        (result,) = c.stack
        self.assertEqual(EngNumber('2k'), result)

    def testArithmetic(self):
        "Arithmetic should work using EngNumbers"
        c = Calculator()
        c.execute('2k')
        c.execute('2k')
        c.execute('+')
        (result,) = c.stack
        self.assertEqual(EngNumber('4k'), result)

    def testImplicitConversion(self):
        """Arithmetic involving an EngNumber and an int should return an
        EngNumber"""
        c = Calculator()
        c.execute('2k')
        c.execute('2000')
        c.execute('+')
        (result,) = c.stack
        self.assertEqual(EngNumber('4k'), result)

    def testNoImplicitConversion(self):
        """An int without suffixes should not be implicitly converted to
        EngNumber"""
        c = Calculator()
        c.execute('2000')
        (result,) = c.stack
        self.assertNotIsInstance(result, EngNumber)

    def testAutomaticUnitScaling(self):
        "EngNumbers should automatically scale to the closest unit"
        c = Calculator()
        c.execute('3m')
        c.execute('3m')
        c.execute('*')
        (result,) = c.stack
        self.assertEqual(EngNumber('9u'), result)
        self.assertEqual(str(EngNumber('9u')), str(result))
