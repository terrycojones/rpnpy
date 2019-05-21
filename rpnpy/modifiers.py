from collections import namedtuple

from rpnpy.errors import UnknownModifiersError, IncompatibleModifiersError


MODIFIERS = {
    '*': 'all',
    'c': 'forceCommand',
    'D': 'debug',
    'i': 'iterate',
    'n': 'noSplit',
    '=': 'preserveStack',
    'p': 'print',
    's': 'split',
    '!': 'push',
}

Modifiers = namedtuple(
    'Modifiers', sorted(MODIFIERS.values()),
    defaults=[False] * len(MODIFIERS))


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
