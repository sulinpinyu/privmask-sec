"""识别器注册表。

新增一种实体类型，只要在这里加一行。引擎会自动带上它。
"""

from .bank_card import BankCardRecognizer
from .base import BaseRecognizer
from .id_card import IdCardRecognizer
from .misc import EmailRecognizer, IpAddressRecognizer
from .phone import PhoneRecognizer

__all__ = [
    "BaseRecognizer",
    "IdCardRecognizer",
    "PhoneRecognizer",
    "BankCardRecognizer",
    "EmailRecognizer",
    "IpAddressRecognizer",
    "build_default_recognizers",
]


def build_default_recognizers() -> list[BaseRecognizer]:
    """返回默认启用的识别器列表。

    顺序不影响结果，引擎会自己做重叠消解。
    """
    return [
        IdCardRecognizer(),
        PhoneRecognizer(),
        BankCardRecognizer(),
        EmailRecognizer(),
        IpAddressRecognizer(),
    ]
