import inspect


def countArgs(func):
    try:
        sig = inspect.signature(func)
    except ValueError:
        return None
    else:
        return len([
            p for p in sig.parameters.values() if
            p.default == inspect.Parameter.empty and
            (p.kind == inspect.Parameter.POSITIONAL_ONLY or
             p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD)])
