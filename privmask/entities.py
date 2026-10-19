"""核心数据结构。

整个项目只围绕一个概念转：Entity（实体）。
一条 Entity 描述的是"文本里某一段是某种敏感信息"。

之所以用 start/end 下标而不是直接替换字符串，是因为：
    1. 同一段文字里可能出现多个相同的手机号，替换时会串位
    2. 需要保留原文位置，前端才能做高亮
    3. 多种识别器可能命中同一区域，需要靠下标判断重叠
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Entity:
    """一段被识别出来的敏感信息。

    Attributes:
        entity_type: 实体类型，如 ID_CARD / PHONE / BANK_CARD / EMAIL / IPV4
        start:       在原文中的起始下标（含）
        end:         在原文中的结束下标（不含）
        text:        命中的原文内容
        score:       置信度 0.0-1.0，用于多识别器冲突时排序
    """

    entity_type: str
    start: int
    end: int
    text: str
    score: float = 1.0

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Entity") -> bool:
        """两段区间是否相交。端点相接不算重叠。"""
        return self.start < other.end and other.start < self.end

    def to_dict(self) -> dict:
        return {
            "type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "score": round(self.score, 2),
        }

    def __str__(self) -> str:
        return f"<{self.entity_type} [{self.start}:{self.end}] {self.text!r}>"
