"""杂项识别器：邮箱、IPv4 地址。

这两类没有校验位，靠正则 + 边界约束控制误报。
"""

import re

from ..entities import Entity
from .base import BaseRecognizer

_EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)"
    r"(?![A-Za-z0-9-])"
)

# 前后不能紧邻数字或点，避免从 1.2.3.4.5 这类版本号里截取
_IPV4_PATTERN = re.compile(r"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?![\d.])")


class EmailRecognizer(BaseRecognizer):
    """电子邮箱识别器。"""

    name = "email"
    entity_types = frozenset({"EMAIL"})

    def analyze(self, text: str) -> list[Entity]:
        results = []

        for match in _EMAIL_PATTERN.finditer(text):
            address = match.group(1)
            # 邮箱总长有上限（RFC 5321 规定 254），超长的多半是拼出来的
            if len(address) > 254:
                continue

            results.append(
                Entity(
                    entity_type="EMAIL",
                    start=match.start(1),
                    end=match.end(1),
                    text=address,
                    score=0.9,
                )
            )

        return results


class IpAddressRecognizer(BaseRecognizer):
    """IPv4 地址识别器。日志脱敏场景下很常用。"""

    name = "ipv4"
    entity_types = frozenset({"IPV4"})

    def analyze(self, text: str) -> list[Entity]:
        results = []

        for match in _IPV4_PATTERN.finditer(text):
            address = match.group(1)
            # 正则只能保证是 1-3 位数字，段值是否在 0-255 还要自己查
            if not all(0 <= int(part) <= 255 for part in address.split(".")):
                continue

            results.append(
                Entity(
                    entity_type="IPV4",
                    start=match.start(1),
                    end=match.end(1),
                    text=address,
                    score=0.8,
                )
            )

        return results
