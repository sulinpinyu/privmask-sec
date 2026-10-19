"""单元测试。

只依赖标准库，跑法：
    python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from privmask import Anonymizer, Engine, summarize  # noqa: E402
from privmask.recognizers.bank_card import luhn_valid  # noqa: E402
from privmask.recognizers.id_card import (  # noqa: E402
    compute_check_code,
    is_valid_birthday,
)


class TestIdCard(unittest.TestCase):
    def test_check_code_matches_standard_example(self):
        # GB 11643 标准里的示例号码：11010519491231002X
        self.assertEqual(compute_check_code("11010519491231002"), "X")

    def test_birthday_validation(self):
        self.assertTrue(is_valid_birthday("19491231"))
        self.assertTrue(is_valid_birthday("20000229"))   # 2000 是闰年
        self.assertFalse(is_valid_birthday("19000229"))  # 1900 不是闰年
        self.assertFalse(is_valid_birthday("19901332"))  # 13 月 32 日
        self.assertFalse(is_valid_birthday("19900431"))  # 4 月没有 31 号

    def test_valid_id_card_detected(self):
        entities = Engine().analyze("身份证号 11010519491231002X 请核验")
        types = [e.entity_type for e in entities]
        self.assertIn("ID_CARD", types)

    def test_wrong_check_digit_rejected(self):
        # 最后一位 X 改成 1，校验必然失败
        entities = Engine().analyze("身份证号 110105194912310021 请核验")
        self.assertNotIn("ID_CARD", [e.entity_type for e in entities])

    def test_invalid_birthday_rejected(self):
        # 13 月，即便校验位算得对也不该认
        first17 = "11010519491331002"
        fake = first17 + compute_check_code(first17)
        entities = Engine().analyze(f"号码 {fake} 结束")
        self.assertNotIn("ID_CARD", [e.entity_type for e in entities])


class TestPhone(unittest.TestCase):
    def test_valid_phone(self):
        entities = Engine().analyze("联系我 13800138000")
        self.assertEqual(len([e for e in entities if e.entity_type == "PHONE"]), 1)

    def test_unknown_prefix_rejected(self):
        # 100 开头的号段不存在
        entities = Engine().analyze("号码 10012345678 结束")
        self.assertEqual([e for e in entities if e.entity_type == "PHONE"], [])

    def test_no_truncation_from_longer_digits(self):
        # 13 位数字不应被截成 11 位手机号
        entities = Engine().analyze("订单号 1380013800012")
        self.assertEqual([e for e in entities if e.entity_type == "PHONE"], [])


class TestBankCard(unittest.TestCase):
    def test_luhn(self):
        self.assertTrue(luhn_valid("4111111111111111"))
        self.assertFalse(luhn_valid("4111111111111112"))

    def test_known_test_card_detected(self):
        entities = Engine().analyze("卡号 4111111111111111")
        self.assertIn("BANK_CARD", [e.entity_type for e in entities])

    def test_all_same_digits_rejected(self):
        entities = Engine().analyze("卡号 1111111111111111")
        self.assertNotIn("BANK_CARD", [e.entity_type for e in entities])


class TestEmailAndIp(unittest.TestCase):
    def test_email(self):
        entities = Engine().analyze("邮箱 zhangsan@example.com 谢谢")
        emails = [e for e in entities if e.entity_type == "EMAIL"]
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0].text, "zhangsan@example.com")

    def test_ipv4_range_check(self):
        entities = Engine().analyze("地址 192.168.1.10 上线")
        self.assertIn("IPV4", [e.entity_type for e in entities])

        # 999 超范围，不该认
        entities = Engine().analyze("版本 999.999.999.999")
        self.assertNotIn("IPV4", [e.entity_type for e in entities])


class TestAnonymizer(unittest.TestCase):
    def setUp(self):
        self.engine = Engine()
        self.text = "手机 13800138000，卡号 4111111111111111"

    def test_mask_strategy(self):
        entities = self.engine.analyze(self.text)
        masked = Anonymizer("mask").anonymize(self.text, entities)
        self.assertIn("138****8000", masked)
        self.assertNotIn("4111111111111111", masked)

    def test_replace_strategy(self):
        entities = self.engine.analyze(self.text)
        masked = Anonymizer("replace").anonymize(self.text, entities)
        self.assertIn("[PHONE]", masked)
        self.assertIn("[BANK_CARD]", masked)

    def test_hash_is_stable(self):
        text = "手机 13800138000"
        entities = self.engine.analyze(text)
        first = Anonymizer("hash").anonymize(text, entities)
        second = Anonymizer("hash").anonymize(text, entities)
        self.assertEqual(first, second)

    def test_redact_keeps_length(self):
        entities = self.engine.analyze("手机 13800138000")
        masked = Anonymizer("redact").anonymize("手机 13800138000", entities)
        self.assertEqual(len(masked), len("手机 13800138000"))

    def test_text_length_preserved_under_mask(self):
        """mask 不能改变文本总长度，否则前端高亮会错位。"""
        entities = self.engine.analyze(self.text)
        masked = Anonymizer("mask").anonymize(self.text, entities)
        self.assertEqual(len(masked), len(self.text))

    def test_summary_counts(self):
        entities = self.engine.analyze("手机 13800138000 和 18612345678")
        self.assertEqual(summarize(entities).get("PHONE"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
