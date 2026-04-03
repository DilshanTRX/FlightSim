"""
number_words.py
Converts numbers ↔ aviation-style spoken words.

 to_spoken_altitude(6000)  → "six thousand"
 to_spoken_speed(240)      → "two four zero"
 to_spoken_heading(180)    → "one eight zero"
 parse_spoken_number("two four zero") → 240
"""

import re

ONES = [
    "zero","one","two","three","four",
    "five","six","seven","eight","nine",
    "ten","eleven","twelve","thirteen","fourteen",
    "fifteen","sixteen","seventeen","eighteen","nineteen",
]
TENS = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]


def _int_to_words(n: int) -> str:
    """Convert integer 0–99 to English words."""
    if n < 0:
        return "minus " + _int_to_words(-n)
    if n < 20:
        return ONES[n]
    tens, ones = divmod(n, 10)
    return TENS[tens] + ("-" + ONES[ones] if ones else "")


def to_spoken_altitude(feet: int) -> str:
    """
    Convert altitude in feet to ATC spoken form.
    6000  → 'six thousand'
    3500  → 'three thousand five hundred'
    """
    feet = int(round(feet / 100) * 100)   # snap to nearest 100 ft
    thousands, remainder = divmod(feet, 1000)
    hundreds = remainder // 100

    parts = []
    if thousands:
        parts.append(_int_to_words(thousands) + " thousand")
    if hundreds:
        parts.append(_int_to_words(hundreds) + " hundred")
    return " ".join(parts) if parts else "zero"


def to_spoken_speed(knots: int) -> str:
    """
    Convert speed to digit-by-digit ATC form.
    240 → 'two four zero'
    """
    return " ".join(ONES[int(d)] for d in str(int(knots)))


def to_spoken_heading(degrees: int) -> str:
    """
    Convert heading to three-digit digit-by-digit ATC form.
    180 → 'one eight zero'
      5 → 'zero zero five'
    """
    padded = f"{int(degrees):03d}"
    return " ".join(ONES[int(d)] for d in padded)


# ---------------------------------------------------------------------------
# Reverse: spoken → integer
# ---------------------------------------------------------------------------

_WORD_TO_INT = {w: i for i, w in enumerate(ONES)}
_WORD_TO_INT.update({w: i * 10 for i, w in enumerate(TENS) if w})
_WORD_TO_INT["hundred"] = 100
_WORD_TO_INT["thousand"] = 1000

# Careful: DO NOT alias "to" to 2 because "climbing to 6000" breaks.
_EXTRA_ALIASES = {
    "niner": 9,
}
_WORD_TO_INT.update(_EXTRA_ALIASES)


def parse_spoken_number(text: str) -> int | None:
    """
    Try to extract an integer from a spoken phrase. (Simple single-number intended).
    Used mostly by tests, readback validation uses extract_numbers_from_text natively.
    """
    nums = extract_numbers_from_text(text)
    if nums:
        return nums[0]
    return None


def extract_numbers_from_text(text: str) -> list[int]:
    """
    Extract all recognisable numbers from a block of text.
    Used by the readback validator to find altitude/speed/heading values.
    """
    numbers = []

    # 1. Bare numerics (e.g. "240", "6000")
    for match in re.finditer(r"\b\d[\d,]*\b", text):
        numbers.append(int(match.group().replace(",", "")))

    words = text.lower().replace("-", " ").split()
    
    # helper for greedy parsing altitude at index i
    def parse_altitude(tokens, start):
        i = start
        val = 0
        current = 0
        consumed = 0
        found_multiplier = False
        while i < len(tokens):
            w = tokens[i]
            v = _WORD_TO_INT.get(w)
            if v is None:
                # specifically handle "thousand" if preceded by numbers
                break
            
            if v == 1000:
                val += current * 1000 if current else 1000
                current = 0
                found_multiplier = True
            elif v == 100:
                current *= 100
                found_multiplier = True
            else:
                current += v
            consumed += 1
            i += 1
        val += current
        # A valid altitude phrase must have a multiplier like thousand or hundred,
        # or it's just a multi-word number that we consumed entirely.
        # e.g., "six thousand" (consumed=2), "one hundred"
        if consumed > 0 and found_multiplier:
            return val, consumed
        return 0, 0

    # 2. Extract sequences
    i = 0
    while i < len(words):
        # A) Try parsing as an altitude (e.g. "six thousand five hundred")
        alt_val, alt_consumed = parse_altitude(words, i)
        if alt_consumed >= 2 and alt_val >= 100:
            numbers.append(alt_val)
            i += alt_consumed
            continue
            
        # B) Try "digit digit digit" (e.g. "two four zero", "too four zero")
        # We allow specific loose aliases only within a sequence to avoid false positives!
        seq = []
        j = i
        while j < len(words):
            w = words[j]
            v = _WORD_TO_INT.get(w)
            # local aliases that are too broad globally
            if v is None:
                if w in ("too", "two"): v = 2
                elif w in ("for", "four"): v = 4
                elif w in ("ate", "eight"): v = 8
            
            if v is not None and v < 10:
                seq.append(v)
                j += 1
            else:
                break
                
        if len(seq) >= 2:
            s_val = int("".join(str(x) for x in seq))
            numbers.append(s_val)
            i = j
            continue
            
        i += 1

    return list(set(numbers))
