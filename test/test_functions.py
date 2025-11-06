from unittest import TestCase

from rpnpy.errors import CalculatorError
from rpnpy.calculator import Calculator


class TestFactorial(TestCase):
    """Test the factorial function"""

    def test_int(self):
        calc = Calculator()
        calc.execute("5")
        calc.execute("factorial")
        self.assertEqual([120], calc.stack)

    def test_integer_float(self):
        """
        Should be able to calculate the factorial of float the value of which doesn't change when
        rounded.
        """
        calc = Calculator()
        calc.execute("5.0")
        calc.execute("factorial")
        self.assertEqual([120], calc.stack)
