from datetime import date, datetime
from decimal import Decimal
from app.config import settings
from app.db.database import readonly_engine
from app.guardrails.sql import validate_sql
from sqlalchemy import text


def _serialize(val):
  if isinstance(val, (datetime, date)):
    return val.isoformat()
  if isinstance(val, Decimal):
    return float(val)
  return val


def execute_sql_query(query: str) -> dict:
  # execute validated select query on readonly database with timeout
  valid, msg = validate_sql(query)
  if not valid:
    return {"error": f"query rejected by safety validator: {msg}"}

  try:
    with readonly_engine.connect() as conn:
      timeout_ms = int(settings.sql_timeout_seconds * 1000)
      conn.execute(text(f"SET statement_timeout = {timeout_ms};"))
      result = conn.execute(text(msg))

      keys = list(result.keys()) if result.returns_rows else []
      if not keys:
        return {"columns": [], "rows": [], "row_count": 0}

      raw_rows = result.fetchmany(settings.sql_row_limit)
      rows = [
          {k: _serialize(v) for k, v in row._mapping.items()}
          for row in raw_rows
      ]

      return {
          "columns": keys,
          "rows": rows,
          "row_count": len(rows),
      }
  except Exception as exc:
    return {"error": f"sql execution failed: {str(exc)}"}
