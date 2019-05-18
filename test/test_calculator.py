from unittest import TestCase

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
        c.execute('operator.abs /!')
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

    def testRegister(self):
        """Registering and calling a new function must work"""
        def double(n):
            return 2 * n

        c = Calculator()
        c.register('module', 'double', double, 1)
        c.execute('3')
        c.execute('double')
        (result,) = c.stack
        self.assertEqual(6, result)
