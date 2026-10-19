"""银行卡号识别器（16-19 位，Luhn 校验）。

========== Luhn 算法（模 10 双倍校验）==========
这是所有银行卡号通用的校验规则，用来发现输错一位的情况。

    Step 1  从最右边一位开始往左数
    Step 2  处于偶数位（从右数第 2、4、6... 位）的数字乘 2
    Step 3  乘积如果大于 9，就减去 9（等价于把十位和个位相加）
    Step 4  全部加起来
    Step 5  总和能被 10 整除，号码才有效

举个能通过的例子：4111 1111 1111 1111
    从右往左，第 2、4、6... 位是 1，乘 2 得 2，累加
    其余位是 1 或 4，原样累加
    总和 = 30，30 % 10 == 0 → 校验通过

举个通不过的例子：4111 1111 1111 1112
    最后一位变成 2，总和变成 31，不能被 10 整除 → 无效

注意：Luhn 只能检出"单个数字写错"和"相邻两位写反"这类错误，
     它不能证明卡号真实存在。所以这里的 score 给得比身份证低。
"""

import re

from ..entities import Entity
from .base import BaseRecognizer

# 16-19 位连续数字，前后不能紧邻数字
_PATTERN = re.compile(r"(?<!\d)(\d{16,19})(?!\d)")


def luhn_valid(number: str) -> bool:
    """判断一串数字是否通过 Luhn 校验。"""
    total = 0

    for index, ch in enumerate(reversed(number)):
        digit = int(ch)
        # index 从 0 开始，所以 index 为奇数表示"从右数第 2、4、6... 位"
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


class BankCardRecognizer(BaseRecognizer):
    """银行卡号识别器。"""

    name = "bank_card"
    entity_types = frozenset({"BANK_CARD"})

    def analyze(self, text: str) -> list[Entity]:
        results = []

        for match in _PATTERN.finditer(text):
            number = match.group(1)

            # 全相同的数字（如 1111111111111111）能通过 Luhn，但不是真卡号
            if len(set(number)) == 1:
                continue
            # 卡号不以 0 开头
            if number[0] == "0":
                continue
            if not luhn_valid(number):
                continue

            results.append(
                Entity(
                    entity_type="BANK_CARD",
                    start=match.start(1),
                    end=match.end(1),
                    text=number,
                    score=0.85,
                )
            )

        return results
