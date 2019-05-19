from unittest import TestCase
from io import StringIO

import operator

from rpnpy import Calculator


class TestCalculator(TestCase):

    def testEmptyStack(self):
        """A calculator must start life with an empty stack"""
        self.assertEqual([], Calculator().stack)

    def testPushNumber(self):
        """Pushing a number must work as expected"""
        c = Calculator()
        c.execute('4')
        (result,) = c.stack
        self.assertEqual(4, result)

    def testPushString(self):
        """Pushing a string must work as expected"""
        c = Calculator()
        c.execute("'4'")
        (result,) = c.stack
        self.assertEqual('4', result)

    def testPushAbs(self):
        """Pushing the operator.abs function must work as expected"""
        c = Calculator()
        c.execute('operator.abs :!')
        (result,) = c.stack
        self.assertIs(operator.abs, result)

    def testAdd(self):
        """Adding must work"""
        c = Calculator()
        c.execute('3')
        c.execute('4')
        c.execute('+')
        (result,) = c.stack
        self.assertEqual(7, result)

    def testAddOneArg(self):
        """Adding must give an error if there is only one thing on the stack"""
        err = StringIO()
        c = Calculator(errfp=err)
        c.execute('3')
        c.execute('+')
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
        c.execute('3')
        c.execute('double')
        (result,) = c.stack
        self.assertEqual(6, result)

    def testRegisterWithArgCount2(self):
        """Registering and calling a new function and passing its argument
           count must work"""
        def doubleMax(*args):
            return 2 * max(*args)

        c = Calculator()
        c.register(doubleMax, name='doubleMax', nArgs=3)
        c.execute('3')
        c.execute('5')
        c.execute('6')
        c.execute('7')
        c.execute('doubleMax')
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
        c.execute('3')
        c.execute('5')
        c.execute('addAndDouble')
        (result,) = c.stack
        self.assertEqual(16, result)

    def testRegisterCelciusNoExplicitName(self):
        """
        Register and call a function to convert Fahrenheit to Celcius but do
        not pass a function name
        """
        def celcius(f):
            return (f - 32) / 1.8

        c = Calculator()
        c.register(celcius)
        c.execute('212')
        c.execute('celcius')
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
        """sum must take one arg by default"""
        c = Calculator()
        self.assertEqual(1, c._functions['sum'].nArgs)

    def testPowTwoArgs(self):
        """pow must take two args by default"""
        c = Calculator()
        self.assertEqual(2, c._functions['pow'].nArgs)

    def testSwap(self):
        """swap must work as expected"""
        c = Calculator()
        c.execute('4')
        c.execute('5')
        self.assertEqual([4, 5], c.stack)
        c.execute('swap')
        self.assertEqual([5, 4], c.stack)
