import re

NUMBER_RE = re.compile(r'(\d+)')


def splitInput(inputLine):
    """Split an input line into a command and modifiers

    @param inputLine: A C{str} input line.
    @return: A 3-tuple containing 1) the C{str} command, stripped of any
        whitespace 2) a C{set} of lower-case modifiers, and 3) an C{int} count
        (or C{None} if no count is found).
    """
    fields = inputLine.rsplit('/', 1)
    try:
        command, modifiers = fields
    except ValueError:
        command = inputLine.strip()
        modifiers = ''
    else:
        command = command.strip()
        modifiers = modifiers.strip()

        if not (command or modifiers):
            # This is a lone / on a line. This indicates division, not
            # an empty command with no modifiers.
            command = '/'

    if command.startswith('#'):
        # This is a comment.
        return '', set(), None

    match = NUMBER_RE.search(modifiers)
    if match:
        count = int(match.group(1))
        modifiers = (modifiers[:match.start(1)].strip() +
                     modifiers[match.end(1):].strip())
    else:
        count = None

    return command.strip(), set(modifiers.strip().lower()), count
