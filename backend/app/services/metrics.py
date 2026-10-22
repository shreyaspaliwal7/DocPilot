from app.db.models import RequestLog
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session


def calculate_metrics(db: Session) -> dict:
  # calculate aggregate metrics and most frequent failed queries
  total = db.query(RequestLog).count()
  if total == 0:
    return {
        "total_requests": 0,
        "average_latency": 0.0,
        "total_estimated_cost": 0.0,
        "failure_rate": 0.0,
        "rate_limit_hit_count": 0,
        "most_common_failed_questions": [],
    }

  avg_lat = db.query(func.avg(RequestLog.latency)).scalar() or 0.0
  total_cost = db.query(func.sum(RequestLog.estimated_cost)).scalar() or 0.0
  failed_count = (
      db.query(RequestLog).filter(RequestLog.success.is_(False)).count()
  )
  rate_limit_count = (
      db.query(RequestLog)
      .filter(RequestLog.error_type == "rate_limit")
      .count()
  )

  failed_query_rows = (
      db.query(
          RequestLog.masked_question,
          func.count(RequestLog.id).label("cnt"),
      )
      .filter(
          or_(RequestLog.success.is_(False), RequestLog.is_not_found.is_(True)),
          RequestLog.masked_question != "",
      )
      .group_by(RequestLog.masked_question)
      .order_by(desc("cnt"))
      .limit(5)
      .all()
  )

  common_failed = [
      {"question": row[0], "count": int(row[1])} for row in failed_query_rows
  ]

  return {
      "total_requests": total,
      "average_latency": round(float(avg_lat), 3),
      "total_estimated_cost": round(float(total_cost), 6),
      "failure_rate": round(float(failed_count / total), 4),
      "rate_limit_hit_count": rate_limit_count,
      "most_common_failed_questions": common_failed,
  }
