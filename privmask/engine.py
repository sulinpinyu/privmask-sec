"""识别引擎。

职责有三件：
    1. 管理一组识别器
    2. 把同一段文本交给所有识别器，收集候选结果
    3. 消解冲突——去掉重叠的实体，避免同一段文字被处理两次
"""

from typing import Iterable, List, Optional, Sequence

from .entities import Entity
from .recognizers import BaseRecognizer, build_default_recognizers


class Engine:
    """敏感信息识别引擎。

    用法：
        engine = Engine()
        for entity in engine.analyze("我的手机号是 13800138000"):
            print(entity)
    """

    def __init__(self, recognizers: Optional[Sequence[BaseRecognizer]] = None) -> None:
        self.recognizers: List[BaseRecognizer] = (
            list(recognizers) if recognizers is not None else build_default_recognizers()
        )

    def analyze(
        self,
        text: str,
        entity_types: Optional[Iterable[str]] = None,
    ) -> List[Entity]:
        """分析文本，返回按位置排序的实体列表。

        Args:
            text: 待分析文本
            entity_types: 只关心这些类型，传 None 表示全部
        """
        if not text:
            return []

        wanted = set(entity_types) if entity_types else None

        candidates: List[Entity] = []
        for recognizer in self.recognizers:
            if wanted is not None and not (recognizer.entity_types & wanted):
                continue
            candidates.extend(recognizer.analyze(text))

        return self._resolve_overlaps(candidates)

    @staticmethod
    def _resolve_overlaps(entities: List[Entity]) -> List[Entity]:
        """消解重叠实体。

        冲突场景举例：
            一段 19 位数字既可能被银行卡识别器命中，
            中间又可能包含一段看起来像手机号的 11 位数字。

        策略：按 "置信度高 → 长度长 → 位置靠前" 排序，
              依次收录不与已收录实体重叠的候选。
        """
        if not entities:
            return []

        ordered = sorted(entities, key=lambda e: (-e.score, -e.length, e.start))

        kept: List[Entity] = []
        for candidate in ordered:
            if any(candidate.overlaps(existing) for existing in kept):
                continue
            kept.append(candidate)

        return sorted(kept, key=lambda e: e.start)
