"""中国大陆手机号识别器。

规则：11 位，1 开头，第二位 3-9。

为什么还要查号段？
    单纯 \\d{11} 的误报率很高。加一层号段前缀校验，
    能把 "1380013800012" 这类被截断的长数字、以及
    "12345678901" 这类明显假的号码过滤掉。

号段说明：号段会随时间增加（比如 192、196、197 都是后来放号的），
    这里收录的是工信部公开的常用号段。漏掉的号段会导致该号识别不出来，
    所以宁可多收一些。
"""

import re

from ..entities import Entity
from .base import BaseRecognizer

# 已启用的号段前缀（前三位）
VALID_PREFIXES = frozenset(
    {
        # 中国移动
        "134", "135", "136", "137", "138", "139",
        "147", "148", "150", "151", "152", "157", "158", "159",
        "172", "178", "182", "183", "184", "187", "188",
        "195", "197", "198",
        # 中国联通
        "130", "131", "132", "145", "146", "155", "156",
        "166", "167", "171", "175", "176", "185", "186",
        "196",
        # 中国电信
        "133", "149", "153", "173", "177", "180", "181", "189",
        "190", "191", "193", "199",
        # 虚拟运营商
        "162", "165", "170",
    }
)

# 前后不允许紧邻数字：防止从 "1380013800012" 里截出 "13800138000"
_PATTERN = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")


class PhoneRecognizer(BaseRecognizer):
    """中国大陆手机号识别器。"""

    name = "phone"
    entity_types = frozenset({"PHONE"})

    def analyze(self, text: str) -> list[Entity]:
        results = []

        for match in _PATTERN.finditer(text):
            number = match.group(1)
            if number[:3] not in VALID_PREFIXES:
                continue

            results.append(
                Entity(
                    entity_type="PHONE",
                    start=match.start(1),
                    end=match.end(1),
                    text=number,
                    score=0.9,
                )
            )

        return results
