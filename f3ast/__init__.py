from .structure import Structure
from .deposit_model import *
from .stream import Stream
from .stream_builder import StreamBuilder
from .solver import DwellSolver
from .utils import *
from .plotting import *
from .calibration import *

from types import ModuleType
import sys
import importlib


def deep_reload(m: ModuleType):
    name = m.__name__  # get the name that is used in sys.modules
    name_ext = name + '.'  # support finding sub modules or packages

    def compare(loaded: str):
        return (loaded == name) or loaded.startswith(name_ext)

    # prevent changing iterable while iterating over it
    all_mods = tuple(sys.modules)
    sub_mods = filter(compare, all_mods)
    for pkg in sorted(sub_mods, key=lambda item: item.count('.'), reverse=True):
        # reload packages, beginning with the most deeply nested
        importlib.reload(sys.modules[pkg])
