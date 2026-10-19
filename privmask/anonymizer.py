"""脱敏处理器。

识别出实体之后，怎么处理由这里决定。提供四种策略：

    replace   整体替换成占位符       13800138000 → [PHONE]
    mask      保留首尾，中间打星号    13800138000 → 138****8000
    hash      取哈希值前 8 位        13800138000 → a3f9c1e2
    redact    全部打星号             13800138000 → ***********

选哪种取决于用途：
    - 对外演示、写文档、发截图 → replace 或 mask
    - 需要保留统计关联（同一个手机号还是同一个）→ hash
    - 彻底不可逆 → redact

为什么要靠实体下标重建字符串，而不是直接 text.replace()？
    因为同一个手机号在文中出现两次，replace 会把两处都换掉；
    而我们需要的是按识别结果精确替换，并且替换后下标不能错位。
"""

import hashlib
from typing import Iterable, List, Optional, Tuple

from .entities import Entity

#: 各类型 mask 策略下保留的首尾字符数 (head, tail)
MASK_WIDTH = {
    "ID_CARD": (6, 4),      # 110105********002X  → 保留地区码和末 4 位
    "PHONE": (3, 4),        # 138****8000
    "BANK_CARD": (4, 4),    # 6222********0128
    "EMAIL": (2, 0),        # zh***@example.com，域名单独处理
    "IPV4": (2, 2),         # 192.168.*.*，段数单独处理
}


def _mask_generic(value: str, head: int, tail: int) -> str:
    if head + tail >= len(value):
        return "*" * len(value)
    middle = "*" * (len(value) - head - tail)
    return value[:head] + middle + (value[-tail:] if tail else "")


def _mask_email(value: str) -> str:
    """邮箱只遮 @ 前面的部分，域名保留——域名本身通常不敏感。"""
    local, _, domain = value.partition("@")
    if not domain:
        return _mask_generic(value, 2, 0)
    if len(local) <= 2:
        masked = local[:1] + "*" * max(len(local) - 1, 1)
    else:
        masked = local[:2] + "*" * (len(local) - 2)
    return f"{masked}@{domain}"


def _mask_ipv4(value: str) -> str:
    """IPv4 保留前两段，后两段打码。既能看出网段，又不暴露具体主机。"""
    parts = value.split(".")
    if len(parts) != 4:
        return _mask_generic(value, 3, 0)
    return ".".join(parts[:2] + ["*", "*"])


class Anonymizer:
    """按策略把实体替换掉。"""

    SUPPORTED_STRATEGIES = ("replace", "mask", "hash", "redact")

    def __init__(self, strategy: str = "mask", salt: str = "") -> None:
        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"未知策略 {strategy!r}，可选：{', '.join(self.SUPPORTED_STRATEGIES)}"
            )
        self.strategy = strategy
        self.salt = salt

    def anonymize(self, text: str, entities: Iterable[Entity]) -> str:
        """用脱敏后的内容重建整段文本。"""
        ordered = sorted(entities, key=lambda e: e.start)
        if not ordered:
            return text

        pieces: List[str] = []
        cursor = 0

        for entity in ordered:
            # 防御：跳过越界或倒序的实体，避免切片错乱
            if entity.start < cursor or entity.end > len(text):
                continue
            pieces.append(text[cursor:entity.start])
            pieces.append(self._apply(entity))
            cursor = entity.end

        pieces.append(text[cursor:])
        return "".join(pieces)

    def _apply(self, entity: Entity) -> str:
        value = entity.text

        if self.strategy == "replace":
            return f"[{entity.entity_type}]"

        if self.strategy == "redact":
            return "*" * len(value)

        if self.strategy == "hash":
            digest = hashlib.sha256((self.salt + value).encode("utf-8")).hexdigest()
            return digest[:8]

        # mask
        if entity.entity_type == "EMAIL":
            return _mask_email(value)
        if entity.entity_type == "IPV4":
            return _mask_ipv4(value)

        head, tail = MASK_WIDTH.get(entity.entity_type, (0, 0))
        return _mask_generic(value, head, tail)


def split_segments(text: str, entities: Iterable[Entity]) -> List[Tuple[str, Optional[Entity]]]:
    """把文本切成"普通片段 / 敏感片段"交替的序列。

    前端高亮就是靠这个：普通片段原样显示，敏感片段套一层高亮样式。
    """
    ordered = sorted(entities, key=lambda e: e.start)
    segments: List[Tuple[str, Optional[Entity]]] = []
    cursor = 0

    for entity in ordered:
        if entity.start < cursor or entity.end > len(text):
            continue
        if entity.start > cursor:
            segments.append((text[cursor:entity.start], None))
        segments.append((text[entity.start:entity.end], entity))
        cursor = entity.end

    if cursor < len(text):
        segments.append((text[cursor:], None))

    return segments


def summarize(entities: Iterable[Entity]) -> dict:
    """按类型统计命中数量，用于报告输出。"""
    counts: dict = {}
    for entity in entities:
        counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
    return dict(sorted(counts.items()))
