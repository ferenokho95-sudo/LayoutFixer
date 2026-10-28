import unittest
from converter import convert, EN, RU, EN_SHIFT, RU_SHIFT


class ConverterTests(unittest.TestCase):
    def test_user_example(self):
        self.assertEqual(convert("ghbdtn"), "привет")

    def test_reverse(self):
        self.assertEqual(convert("руддщ"), "hello")

    def test_case(self):
        self.assertEqual(convert("Ghbdtn"), "Привет")
        self.assertEqual(convert("GHBDTN"), "ПРИВЕТ")

    def test_multiline_and_unicode(self):
        self.assertEqual(convert("ghbdtn\n123 😀\tGhbdtn"), "привет\n123 😀\tПривет")

    def test_no_letters(self):
        self.assertEqual(convert("123 😀 .,/"), "123 😀 .,/")
        self.assertEqual(convert(""), "")

    def test_explicit_punctuation(self):
        self.assertEqual(convert(".,/", "en_ru"), "юб.")
        self.assertEqual(convert(".,", "ru_en"), "/?")

    def test_full_map_roundtrip(self):
        self.assertEqual(convert(EN + EN_SHIFT, "en_ru"), RU + RU_SHIFT)
        self.assertEqual(convert(RU + RU_SHIFT, "ru_en"), EN + EN_SHIFT)

    def test_mixed_direction(self):
        self.assertEqual(convert("ghbdtn мир"), "привет мир")
        self.assertEqual(convert("hello привет"), "hello ghbdtn")

    def test_explicit_override(self):
        self.assertEqual(convert("hello", "ru_en"), "hello")

    def test_bad_direction(self):
        with self.assertRaises(ValueError):
            convert("test", "typo")


if __name__ == "__main__":
    unittest.main()
