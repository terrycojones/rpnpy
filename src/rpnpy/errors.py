class CalculatorError(Exception):
    'An error occurred in executing a command.'


class UnknownModifiersError(Exception):
    'Unknown modifier given in a command.'


class IncompatibleModifiersError(Exception):
    'An incompatible set of modifiers was given in a command.'


class StackError(Exception):
    'An error occurred while examining the stack for arguments'
