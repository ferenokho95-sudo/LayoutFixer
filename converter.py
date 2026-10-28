"""Keyboard-position conversion between US QWERTY and Russian ЙЦУКЕН."""
import re

EN = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
RU = "ёйцукенгшщзхъфывапролджэячсмитьбю."
EN_SHIFT = '~QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?'
RU_SHIFT = 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,'
TO_RU = str.maketrans(EN + EN_SHIFT, RU + RU_SHIFT)
TO_EN = str.maketrans(RU + RU_SHIFT, EN + EN_SHIFT)


def convert(text: str, direction: str = "auto") -> str:
    """Auto chooses one direction for the entire selection, not each word.

    Ties prefer EN → RU. Numbers, emoji and nonmapped characters are kept.
    This is a keyboard map, not transliteration or a spelling dictionary.
    """
    if direction not in ("auto", "en_ru", "ru_en"):
        raise ValueError("Unknown direction")
    if direction == "auto":
        latin = len(re.findall(r"[A-Za-z]", text))
        cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
        if not latin and not cyrillic:
            return text
        direction = "ru_en" if cyrillic > latin else "en_ru"
    return text.translate(TO_RU if direction == "en_ru" else TO_EN)
