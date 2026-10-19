"""识别器基类。

每个识别器负责回答一个问题："这段文本里，哪些片段是 X？"
新增一种实体类型，只需要写一个子类，然后在 recognizers/__init__.py 里注册。
"""

from typing import List

from ..entities import Entity


class BaseRecognizer:
    """所有识别器的父类。"""

    #: 识别器名称，出现在日志和调试信息里
    name: str = "base"

    #: 该识别器可能输出的实体类型集合
    entity_types: frozenset = frozenset()

    def analyze(self, text: str) -> List[Entity]:
        """返回该识别器在 text 中命中的全部实体。"""
        raise NotImplementedError
