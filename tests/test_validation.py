import unittest
import utils

class TestValidation(unittest.TestCase):
    def test_valid_national_ids(self):
        # Mathematically valid Iranian National IDs
        valid_ids = [
            "0010340890",  # sum=88, rem=0 -> check=0
            "0499370899",  # sum=266, rem=2 -> check=9
            "1234567891",  # sum=210, rem=1 -> check=1
            "0078652391",  # sum=208, rem=10 -> check=1
        ]
        for nid in valid_ids:
            is_valid, msg = utils.validate_national_id(nid)
            self.assertTrue(is_valid, f"Expected {nid} to be valid, got: {msg}")
            self.assertEqual(msg, "")

    def test_invalid_national_ids(self):
        # Invalid check digits or bad formats
        invalid_ids = [
            ("0010340899", "کد ملی وارد شده معتبر نیست"),  # Check digit is 0, not 9
            ("1234567890", "کد ملی وارد شده معتبر نیست"),  # Check digit is 1, not 0
            ("1111111111", "همه ارقام یکسان"),
            ("123", "۱۰ رقمی"),
            ("abcdefghij", "فقط شامل اعداد"),
            ("", "نمی‌تواند خالی باشد"),
        ]
        for nid, expected_snippet in invalid_ids:
            is_valid, msg = utils.validate_national_id(nid)
            self.assertFalse(is_valid, f"Expected {nid} to be invalid")
            self.assertIn(expected_snippet, msg)

    def test_foreign_national_codes(self):
        # Universal code for foreign nationals (9, 11, or 12 digits)
        valid_foreign = ["123456789", "123456789012", "98765432109"]
        for fid in valid_foreign:
            is_valid, msg = utils.validate_national_id(fid)
            self.assertTrue(is_valid, f"Expected foreign national ID {fid} to be valid, got: {msg}")

        # Invalid all-same-digits foreign code
        is_valid, msg = utils.validate_national_id("999999999")
        self.assertFalse(is_valid)
        self.assertIn("همه ارقام یکسان", msg)

    def test_persian_name_validation(self):
        valid_names = [
            "علی رضایی",
            "محمدحسین سهرابی",
            "ژاله صادقی",
            "گودرز پناهی",
            "John Doe",
        ]
        for name in valid_names:
            is_valid, msg = utils.validate_persian_name(name)
            self.assertTrue(is_valid, f"Expected {name} to be valid, got: {msg}")

        invalid_names = [
            ("", "حداقل ۲ کاراکتر"),
            ("ا", "حداقل ۲ کاراکتر"),
            ("12345", "شامل حروف"),
            ("@#$%", "شامل حروف"),
        ]
        for name, expected_err in invalid_names:
            is_valid, msg = utils.validate_persian_name(name)
            self.assertFalse(is_valid, f"Expected {name} to be invalid")
            self.assertIn(expected_err, msg)

    def test_numeric_validation(self):
        self.assertTrue(utils.validate_numeric(""))
        self.assertTrue(utils.validate_numeric("1234567890"))
        self.assertTrue(utils.validate_numeric("123456789012"))  # 12 digits max
        self.assertFalse(utils.validate_numeric("1234567890123"))  # 13 digits too long
        self.assertFalse(utils.validate_numeric("123a"))

if __name__ == "__main__":
    unittest.main()
