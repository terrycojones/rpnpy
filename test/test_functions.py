from rpnpy.calculator import Calculator
import math

def test_sin():
    calc = Calculator()
    calc.execute(f"{math.pi / 2}")
    calc.execute("sin")
    assert calc.stack == [1.0]

def test_cos():
    calc = Calculator()
    calc.execute(f"{math.pi}")
    calc.execute("cos")
    assert calc.stack == [-1.0]

def test_tan():
    calc = Calculator()
    calc.execute(f"{math.pi / 4}")
    calc.execute("tan")
    assert math.isclose(calc.stack[0], 1.0)

def test_factorial():
    calc = Calculator()
    calc.execute("5")
    calc.execute("factorial")
    assert calc.stack == [120]
