"""
Validation Functions for Baby Timeline
Reusable validation logic for user inputs.
"""

from typing import Tuple
from src.constants import (
    MIN_WEIGHT_KG,
    MAX_WEIGHT_KG,
    MIN_HEIGHT_CM,
    MAX_HEIGHT_CM,
    MAX_NOTES_LENGTH,
    MAX_CAPTION_LENGTH,
    MIN_PASSWORD_LENGTH
)


def validate_weight(weight_kg: float) -> Tuple[bool, str]:
    """
    Validate baby weight measurement.

    Args:
        weight_kg: Weight in kilograms

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string

    Examples:
        >>> validate_weight(3.5)
        (True, "")
        >>> validate_weight(100)
        (False, "❌ Weight must be between 0.5 and 50.0 kg")
    """
    if weight_kg < MIN_WEIGHT_KG or weight_kg > MAX_WEIGHT_KG:
        return False, f"❌ Weight must be between {MIN_WEIGHT_KG} and {MAX_WEIGHT_KG} kg"
    return True, ""


def validate_height(height_cm: float) -> Tuple[bool, str]:
    """
    Validate baby height measurement.

    Args:
        height_cm: Height in centimeters

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string

    Examples:
        >>> validate_height(50)
        (True, "")
        >>> validate_height(250)
        (False, "❌ Height must be between 30 and 200 cm")
    """
    if height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM:
        return False, f"❌ Height must be between {MIN_HEIGHT_CM} and {MAX_HEIGHT_CM} cm"
    return True, ""


def validate_notes(notes: str) -> Tuple[bool, str]:
    """
    Validate measurement notes length.

    Args:
        notes: Notes text

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string
    """
    if len(notes) > MAX_NOTES_LENGTH:
        return False, f"❌ Notes too long. Maximum {MAX_NOTES_LENGTH} characters."
    return True, ""


def validate_caption(caption: str) -> Tuple[bool, str]:
    """
    Validate photo caption length.

    Args:
        caption: Caption text

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string
    """
    if len(caption) > MAX_CAPTION_LENGTH:
        return False, f"❌ Caption too long. Maximum {MAX_CAPTION_LENGTH} characters."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate share link password.

    Args:
        password: Password string

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message is empty string
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"❌ Password too short. Use at least {MIN_PASSWORD_LENGTH} characters."
    return True, ""
