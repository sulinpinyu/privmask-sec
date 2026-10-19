"""privmask —— 面向中文场景的敏感信息识别与脱敏工具。

使用：
    from privmask import Engine, Anonymizer

    engine = Engine()
    anonymizer = Anonymizer(strategy="mask")

    text = "联系我 13800138000"
    entities = engine.analyze(text)
    print(anonymizer.anonymize(text, entities))
"""

from .anonymizer import Anonymizer, split_segments, summarize
from .entities import Entity
from .engine import Engine

__version__ = "0.1.0"

__all__ = [
    "Engine",
    "Anonymizer",
    "Entity",
    "split_segments",
    "summarize",
]
