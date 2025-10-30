from rpnpy.errors import UnknownModifiersError, IncompatibleModifiersError


MODIFIERS = {
    '*': 'all',
    'c': 'forceCommand',
    'D': 'debug',
    'i': 'iterate',
    'n': 'noSplit',
    '=': 'preserveStack',
    'p': 'print',
    'P': 'autoPrint',
    '!': 'push',
    'r': 'reverse',
    's': 'split',
}


class Modifiers:
    "Hold information about command modifiers."

    def __init__(self, all=False, forceCommand=False, debug=False,
                 iterate=False, noSplit=False, preserveStack=False,
                 print=False, autoPrint=False, push=False, reverse=False,
                 split=False):
        self.all = all
        self.forceCommand = forceCommand
        self.debug = debug
        self.iterate = iterate
        self.noSplit = noSplit
        self.preserveStack = preserveStack
        self.print = print
        self.autoPrint = autoPrint
        self.push = push
        self.reverse = reverse
        self.split = split

    def __eq__(self, other):
        return all((
            self.all == other.all,
            self.forceCommand == other.forceCommand,
            self.debug == other.debug,
            self.iterate == other.iterate,
            self.noSplit == other.noSplit,
            self.preserveStack == other.preserveStack,
            self.print == other.print,
            self.autoPrint == other.autoPrint,
            self.push == other.push,
            self.reverse == other.reverse,
            self.split == other.split,
        ))


def strToModifiers(s):
    """
    Convert a string of modifier letters into a Modifier instance.

    @param s: A C{str} of modifier letters.
    @return: A C{Modifier} instance.
    """
    d = {}
    unknown = []
    for letter in set(s):
        try:
            name = MODIFIERS[letter]
        except KeyError:
            unknown.append(letter)
        else:
            d[name] = True

    if unknown:
        raise UnknownModifiersError(*sorted(unknown))

    modifiers = Modifiers(**d)

    # Test for incompatible modifiers.
    if modifiers.push:
        if modifiers.preserveStack:
            raise IncompatibleModifiersError(
                '= (preserve stack) makes no sense with ! (push)')

    if modifiers.split and modifiers.noSplit:
        raise IncompatibleModifiersError(
            's (split lines) makes no sense with n (do not split lines)')

    return modifiers
