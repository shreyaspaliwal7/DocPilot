import re

DESTRUCTIVE_PATTERN = re.compile(
    r"\b(delete|drop|truncate|alter|erase|wipe|remove)\s+(all\s+)?(customers?|orders?|products?|database|tables?|records?|data)\b"
    r"|\b(drop\s+database|drop\s+table|delete\s+from|delete\s+all)\b"
    r"|\b(insert\s+into|update\s+\w+\s+set)\b",
    re.IGNORECASE,
)

INJECTION_PATTERN = re.compile(
    r"\b(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+instructions\b"
    r"|\b(system\s+override|developer\s+mode|dan\s+mode|jailbreak)\b"
    r"|\b(bypass\s+(safety|rules|guardrails|guidelines))\b"
    r"|\b(reveal\s+(system\s+prompt|your\s+instructions))\b",
    re.IGNORECASE,
)


def check_request_safety(text: str) -> tuple[bool, str]:
  # check for destructive intents and prompt injection attempts before invoking models
  if not text or not text.strip():
    return True, ""

  if DESTRUCTIVE_PATTERN.search(text):
    return False, "i cannot fulfill requests to modify, delete, or alter data."

  if INJECTION_PATTERN.search(text):
    return False, "i cannot process requests attempting to override system guidelines."

  return True, ""
