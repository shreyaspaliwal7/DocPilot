import re

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
CARD_ACCOUNT_PATTERN = re.compile(
    r"\b(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,7}|\d{4}[ -]\d{6}[ -]\d{4,5}|\d{13,19})\b"
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b"
)


def mask_pii(text: str) -> str:
  # mask sensitive personal data before logging or sending to models
  if not text:
    return ""

  masked = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
  masked = CARD_ACCOUNT_PATTERN.sub("[REDACTED_NUMBER]", masked)
  masked = PHONE_PATTERN.sub("[REDACTED_PHONE]", masked)
  return masked
