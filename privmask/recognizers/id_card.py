"""中国大陆居民身份证识别器（18 位）。

为什么要做校验，而不是只写一个正则？

    正则 \\d{17}[\\dX] 会把 "123456789012345678" 这种订单号也当成身份证。
    身份证最后一位不是随机的，它是由前 17 位按固定算法算出来的校验码。
    只要把算出来的校验码和实际最后一位对比，就能过滤掉绝大多数误报。

依据标准：GB 11643-1999《公民身份号码》
========== 号码结构 ==========
    6 位  地址码    → 省(2) + 市(2) + 区县(2)
    8 位  出生日期码 → YYYYMMDD
    3 位  顺序码    → 同一地区同一天出生的人的顺序，奇数为男偶数为女
    1 位  校验码    → 由前 17 位计算得出，取值为 0-9 和 X

========== 校验算法（ISO 7064:1983 MOD 11-2）==========
    Step 1  前 17 位数字分别乘以对应权重，求和
    Step 2  和除以 11，取余数（0-10）
    Step 3  用余数去查校验码表

    举一个例子：110105 19491231 002 X
        数字: 1  1  0  1  0  5  1  9  4  9  1  2  3  1  0  0  2
        权重: 7  9 10  5  8  4  2  1  6  3  7  9 10  5  8  4  2
        相乘: 7  9  0  5  0 20  2  9 24 27  7 18 30  5  0  0  4
        求和 = 167
        167 % 11 = 2
        校验码表中下标 2 是 "X"，与实际末位一致 → 校验通过
"""

import re

from ..entities import Entity
from .base import BaseRecognizer

# 前 17 位的加权因子，这是标准里写死的常数，不要改
WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)

# 余数 0-10 对应的校验码字符，顺序也是标准写死的
CHECK_CODES = ("1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2")

# 有效的省级行政区代码前两位
PROVINCE_CODES = frozenset(
    {
        "11", "12", "13", "14", "15",                                  # 华北
        "21", "22", "23",                                              # 东北
        "31", "32", "33", "34", "35", "36", "37",                      # 华东
        "41", "42", "43", "44", "45", "46",                            # 中南
        "50", "51", "52", "53", "54",                                  # 西南
        "61", "62", "63", "64", "65",                                  # 西北
        "71",                                                          # 台湾
        "81", "82",                                                    # 香港、澳门
        "91",                                                          # 国外
    }
)

# 前后不允许紧邻数字或字母，避免从更长的串里截取出 18 位
_PATTERN = re.compile(
    r"(?<![0-9A-Za-z])"
    r"([1-9]\d{5})"      # 地址码：首位不为 0
    r"(\d{8})"           # 出生日期
    r"(\d{3})"           # 顺序码
    r"([0-9Xx])"         # 校验码
    r"(?![0-9A-Za-z])"
)


def compute_check_code(first17: str) -> str:
    """由前 17 位算出应有的校验码。"""
    total = sum(int(ch) * weight for ch, weight in zip(first17, WEIGHTS))
    return CHECK_CODES[total % 11]


def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0


def is_valid_birthday(yyyymmdd: str) -> bool:
    """检查 8 位日期是否真实存在，能挡掉 19901332 这种。"""
    year = int(yyyymmdd[0:4])
    month = int(yyyymmdd[4:6])
    day = int(yyyymmdd[6:8])

    if not 1900 <= year <= 2100:
        return False
    if not 1 <= month <= 12:
        return False

    days_in_month = (
        31,
        29 if is_leap_year(year) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
    )
    return 1 <= day <= days_in_month[month - 1]


class IdCardRecognizer(BaseRecognizer):
    """18 位居民身份证识别器。"""

    name = "id_card"
    entity_types = frozenset({"ID_CARD"})

    def analyze(self, text: str) -> list[Entity]:
        results = []

        for match in _PATTERN.finditer(text):
            first17 = match.group(1) + match.group(2) + match.group(3)
            check_code = match.group(4).upper()

            # 三道校验，任何一道不过就丢弃
            if first17[:2] not in PROVINCE_CODES:
                continue
            if not is_valid_birthday(match.group(2)):
                continue
            if compute_check_code(first17) != check_code:
                continue

            results.append(
                Entity(
                    entity_type="ID_CARD",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(0),
                    score=0.95,
                )
            )

        return results
