import re

from rpnpy.modifiers import strToModifiers, Modifiers, MODIFIERS


_NUMBER_RE = re.compile(r'(\d+)')
_MODIFIERS_SEPARATOR = ':'


def findModifiers(line):
    """Find the modifiers (if any) in an input line.

    @param line: A C{str} input line.
    @return: A 3-C{tuple} with the C{int} offset of the modifier separator
        in C{line} or -1 if no modifier is found, a C{Modifiers} instance,
        and an C{int} count (or C{None} if no count is found).
    """
    index = line.rfind(_MODIFIERS_SEPARATOR)

    if index == -1:
        return -1, Modifiers(), None

    line = line[index + 1:]

    # Look for a number and extract it if present.
    match = _NUMBER_RE.search(line)
    if match:
        count = int(match.group(1))
        line = line[:match.start(1)] + line[match.end(1):]
    else:
        count = None

    # Examine all the other characters.
    #
    # We only consider this to be a valid set of modifiers if the letters
    # are all in MODIFIERS. Be slightly lenient and allow repeated letters.
    seen = set()
    for letter in line:
        if letter in MODIFIERS:
            seen.add(letter)
        elif not letter.isspace():
            break
    else:
        return index, strToModifiers(''.join(seen)), count

    # Even though we found the modifier separator, there are unknown
    # characters that follow it, so we conclude that this is not actually
    # an attempt to give modifier. E.g., in {'a': 27, 'b': 77} there is
    # a colon but it's followed by a '}' so we reject.
    return -1, Modifiers(), None


def findCommands(line, splitLines=True, separator=None):
    """Find all commands (and their modifiers) in an input line.

    @param line: A C{str} input line.
    @param splitLines: If C{True}, split lines using C{separator}.
    @param separator: A C{str} to split the line into individual commands
        with, or C{None} to indicate whitespace splitting.
    """
    fields = line.strip().split(separator) if splitLines else [line.strip()]
    fieldIndex = 0

    while True:
        try:
            field = fields[fieldIndex]
        except IndexError:
            break

        index, modifiers, count = findModifiers(field)

        if index == -1:
            # This field has no modifiers. Check for them at the very start
            # of the next field. This allows a command and its modifiers to
            # be separated by whitespace, even when line splitting is on.
            try:
                nextField = fields[fieldIndex + 1]
            except IndexError:
                index = -1
            else:
                index, nextModifiers, nextCount = findModifiers(nextField)
            if index == 0:
                modifiers = nextModifiers
                count = nextCount
                fieldIndex += 1
            command = field
        else:
            command = field[:index].strip()

        if command and command.startswith('#'):
            # This is a comment. Return an empty command and break.
            yield '', modifiers, count
            break

        yield command, modifiers, count

        fieldIndex += 1
