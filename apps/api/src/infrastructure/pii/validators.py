"""Validators that reduce false positives for number-based PII.

Implements the official check-digit algorithms for the Japanese Individual
Number (マイナンバー) and Corporate Number (法人番号), plus Luhn for cards and
octet-range validation for IPv4.
"""

from __future__ import annotations


def only_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def luhn_valid(value: str) -> bool:
    digits = only_digits(value)
    if not (13 <= len(digits) <= 19):
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def mynumber_valid(value: str) -> bool:
    """Japanese Individual Number: 11 payload digits + 1 check digit (12 total)."""
    digits = only_digits(value)
    if len(digits) != 12:
        return False
    body = [int(c) for c in digits[:11]]
    check = int(digits[11])
    # P_n counts from the least-significant payload digit (n=1..11).
    total = 0
    for n in range(1, 12):
        p = body[11 - n]
        q = n + 1 if n <= 6 else n - 5
        total += p * q
    r = total % 11
    expected = 0 if r <= 1 else 11 - r
    return expected == check


def corporate_number_valid(value: str) -> bool:
    """Japanese Corporate Number: 1 check digit + 12 payload digits (13 total)."""
    digits = only_digits(value)
    if len(digits) != 13:
        return False
    check = int(digits[0])
    body = [int(c) for c in digits[1:]]  # n1..n12 (left to right)
    total = 0
    for n in range(1, 13):
        p = body[12 - n]  # from least-significant payload digit
        q = 1 if n % 2 == 1 else 2
        total += p * q
    expected = 9 - (total % 9)
    return expected == check


def ipv4_valid(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
