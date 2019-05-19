import re

from rpnpy.modifiers import strToModifiers


_NUMBER_RE = re.compile(r'(\d+)')
_SEPARATOR = ':'


def splitInput(line, separator=None):
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
    fields = line.rsplit(_SEPARATOR, 1)
    try:
        commands, modifiers = fields
    except ValueError:
        commands = line.strip()
        modifiers = ''
    else:
        commands = commands.strip()
        modifiers = modifiers.strip()

    if not commands or commands.startswith('#'):
        # This is an empty input line or a comment.
        yield (None, None, None)
    else:
        match = _NUMBER_RE.search(modifiers)
        if match:
            count = int(match.group(1))
            modifiers = (modifiers[:match.start(1)].strip() +
                         modifiers[match.end(1):].strip())
        else:
            count = None

        modifiers = strToModifiers(modifiers)
        if modifiers.noSplit:
            yield (commands, modifiers, count)
        else:
            for command in commands.split(separator):
                yield command.strip(), modifiers, count
