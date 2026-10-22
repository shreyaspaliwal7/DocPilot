import re

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|execute|copy|vacuum|into|call|rename)\b",
    re.IGNORECASE,
)


def validate_sql(raw_query: str) -> tuple[bool, str]:
  # verify query is a single readonly select statement without comments or modifications
  if not raw_query or not raw_query.strip():
    return False, "query cannot be empty"

  query = raw_query.strip()

  if "--" in query or "/*" in query or "*/" in query:
    return False, "sql comments are not allowed"

  trimmed = query.rstrip(";").strip()
  if ";" in trimmed:
    return False, "multiple statements are not allowed"

  if not trimmed.lower().startswith("select"):
    return False, "only select statements are allowed"

  match = FORBIDDEN_KEYWORDS.search(trimmed)
  if match:
    return False, f"disallowed keyword in query: {match.group(0)}"

  return True, trimmed
