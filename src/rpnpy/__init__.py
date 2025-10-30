from importlib.metadata import PackageNotFoundError, version

from .calculator import Calculator

try:
    __version__ = version("rpnpy")
except PackageNotFoundError:
    # Package is not installed.
    __version__ = "unknown"


# Keep Python linters quiet.
_ = Calculator

__all__ = ["Calculator"]
