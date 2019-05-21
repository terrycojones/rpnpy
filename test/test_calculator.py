import sys
from unittest import TestCase
from io import StringIO

import operator

from rpnpy import Calculator


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

    def testIterateGenerator(self):
        "The :i (iterate) modifier must work as expected on a generator"
        c = Calculator()
        c.execute('str :!')
        c.execute('[1,2,3]')
        c.execute('map :i')
        (result,) = c.stack
        self.assertEqual(['1', '2', '3'], result)

    def testItemgetter(self):
        "itemgetter must work correctly"
        c = Calculator(splitLines=False)
        c.execute('1')
        c.execute('itemgetter')
        c.execute('[[1, 2, 3], [4, 5, 6]]')
        c.execute('map :i')
        (result,) = c.stack
        self.assertEqual([2, 5], result)

    def testApplyNoCount(self):
        "apply must work correctly when not given a count"
        c = Calculator()
        c.execute('-1')
        c.execute('abs :!')
        c.execute('apply')
        (result,) = c.stack
        self.assertEqual(1, result)

    def testApplyWithCount(self):
        "apply must work correctly when given a count"
        c = Calculator()
        c.execute('3 5')
        c.execute('+ :!')
        c.execute('apply :2')
        (result,) = c.stack
        self.assertEqual(8, result)

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
