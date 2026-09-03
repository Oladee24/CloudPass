import re
from decimal import Decimal, InvalidOperation


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(ValueError):
    pass


def require_fields(payload, fields):
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")


def normalize_email(value):
    email = str(value or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise ValidationError("A valid email address is required")
    return email


def normalize_text(value, field_name):
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{field_name} cannot be empty")
    return text


def positive_int(value, field_name):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a positive integer") from exc

    if number <= 0:
        raise ValidationError(f"{field_name} must be a positive integer")
    return number


def positive_decimal(value, field_name):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValidationError(f"{field_name} must be a positive amount") from exc

    if number <= 0:
        raise ValidationError(f"{field_name} must be a positive amount")
    return number
