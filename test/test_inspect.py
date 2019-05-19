from unittest import TestCase
from math import log

from rpnpy.inspect import countArgs


class TestCountArgs(TestCase):
    """Test the countArgs function"""

    def testZero(self):
        "A function that takes zero arguments must be processed correctly"
        self.assertEqual(0, countArgs(lambda: 3))

    def testOne(self):
        "A function that takes one argument must be processed correctly"
        self.assertEqual(1, countArgs(lambda x: 3))

    def testTwo(self):
        "A function that takes two arguments must be processed correctly"
        self.assertEqual(2, countArgs(lambda x, y: 3))

    def testLog(self):
        "The signature of math.log can't be inspected (at least in Python 3.7)"
        self.assertEqual(None, countArgs(log))
