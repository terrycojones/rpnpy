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


def splitInput(line, splitLines=True, separator=None):
    """Split an input line into a command and modifiers

    @param line: A C{str} input line.
    @param separator: A C{str} to split the line into individual commands
        with, or C{None} to indicate whitespace splitting.
    @return: A generator that yields 3-C{tuple}s, each containing:
            1) a C{str} command, stripped of any leading/trailing whitespace,
            2) a C{Modifiers} instance, and
            3) an C{int} count or C{None} if no count is found.
        If the input line is empty or is a comment (i.e., starts with #), all
        three returned values are C{None}.
    """
    index, modifiers, count = findModifiers(line)
    commands = (line if index == -1 else line[:index]).strip()

    if not commands or commands.startswith('#'):
        # This is an empty input line or a comment.
        yield (None, None, None)
    else:
        if splitLines:
            if modifiers.noSplit:
                yield (commands, modifiers, count)
            else:
                for command in commands.split(separator):
                    yield command.strip(), modifiers, count
        else:
            if modifiers.split:
                for command in commands.split(separator):
                    yield command.strip(), modifiers, count
            else:
                yield (commands, modifiers, count)
