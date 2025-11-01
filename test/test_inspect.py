from math import log
from unittest import TestCase

from rpnpy.inspect import countArgs


class TestCountArgs(TestCase):
    """Test the countArgs function"""

    def testZero(self):
        "A function that takes zero arguments must be processed correctly"
        self.assertEqual(0, countArgs(lambda: 3))

    def testOne(self):
        "A function that takes one argument must be processed correctly"
        self.assertEqual(1, countArgs(lambda _: 3))

    def testTwo(self):
        "A function that takes two arguments must be processed correctly"
        self.assertEqual(2, countArgs(lambda a, b: 3 + a + b))

    def testLog(self):
        "The signature of math.log can't be inspected (at least in Python 3.7)"
        self.assertEqual(None, countArgs(log))

    def testLogWithDefault(self):
        """The signature of math.log can't be inspected (at least in Python
        3.7). Pass a default value."""
        self.assertEqual(3, countArgs(log, 3))
