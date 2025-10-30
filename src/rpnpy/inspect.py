import inspect
from typing import Callable, Optional


def countArgs(func: Callable, default: Optional[int] = None) -> Optional[int]:
    try:
        sig = inspect.signature(func)
    except ValueError:
        return default
    else:
        return len(
            [
                p
                for p in sig.parameters.values()
                if p.default == inspect.Parameter.empty
                and (
                    p.kind == inspect.Parameter.POSITIONAL_ONLY
                    or p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                )
            ]
        )
