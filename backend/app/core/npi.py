"""National Provider Identifier (NPI) check-digit validation."""

from __future__ import annotations


def is_valid_npi(npi: str) -> bool:
    """Return True when value is a 10-digit NPI with a valid Luhn check digit."""
    if len(npi) != 10 or not npi.isdigit():
        return False
    return _luhn_checksum_valid(f"80840{npi}")


def _luhn_checksum_valid(number: str) -> bool:
    """Validate a numeric string using the Luhn algorithm."""
    total = 0
    for index, char in enumerate(reversed(number)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
