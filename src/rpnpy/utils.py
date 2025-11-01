import os


def plural(n: int) -> str:
    return "" if n == 1 else "s"


def interactive() -> bool:
    return os.isatty(0)
