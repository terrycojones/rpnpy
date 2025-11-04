import inspect
from typing import Callable, Optional


def countArgs(func: Callable, default: Optional[int] = None) -> Optional[int]:
    try:
        sig = inspect.signature(func)
    except ValueError:
        return default

    # Return -1 if the function can take arbitrarily many args. That will cause the
    # function to consume all stack items unless a numeric modifier is used.
    if any(
        param.kind == inspect.Parameter.VAR_POSITIONAL
        for param in sig.parameters.values()
    ):
        return -1

    return len(
        [
            param
            for param in sig.parameters.values()
            if param.default == inspect.Parameter.empty
            and (
                param.kind == inspect.Parameter.POSITIONAL_ONLY
                or param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            )
        ]
    )
