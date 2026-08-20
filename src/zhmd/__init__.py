"""zhmd — a descriptive scale for metadiscourse markers in Chinese academic writing.

中文學術寫作後設論述標記的描述性量尺。**這不是偵測器**，見 README 的「What this is not」。
"""
from .markers import (MARKERS, INTERACTIVE_MARKERS, INTERACTIONAL_MARKERS,
                      count, find, han_length)
from .profile import profile, load_reference
from . import stats

__version__ = "1.0.0"
__all__ = ["MARKERS", "INTERACTIVE_MARKERS", "INTERACTIONAL_MARKERS",
           "count", "find", "han_length", "profile", "load_reference", "stats"]
