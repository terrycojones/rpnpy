import atexit

try:
    import gnureadline as readline
except ImportError:
    import readline


def setupReadline(histfile) -> None:
    """Initialize the readline library and command history."""

    try:
        readline.read_history_file(histfile)
        historyLen = readline.get_current_history_length()
    except FileNotFoundError:
        open(histfile, "wb").close()
        historyLen = 0

    def saveHistory(prevHistoryLen: int, histfile: str) -> None:
        newHistoryLen = readline.get_current_history_length()
        readline.set_history_length(1000)
        readline.append_history_file(newHistoryLen - prevHistoryLen, histfile)

    atexit.register(saveHistory, historyLen, histfile)
