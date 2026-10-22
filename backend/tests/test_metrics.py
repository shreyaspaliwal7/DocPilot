from app.db.models import RequestLog
from app.services.metrics import calculate_metrics
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_test_db():
  engine = create_engine("sqlite:///:memory:")
  RequestLog.__table__.create(bind=engine)
  session_factory = sessionmaker(bind=engine)
  return session_factory()


def test_metrics_empty_database():
  db = get_test_db()
  res = calculate_metrics(db)
  assert res["total_requests"] == 0
  assert res["average_latency"] == 0.0
  assert res["total_estimated_cost"] == 0.0
  assert res["failure_rate"] == 0.0
  assert res["rate_limit_hit_count"] == 0
  assert res["most_common_failed_questions"] == []


def test_metrics_aggregation():
  db = get_test_db()

  logs = [
      RequestLog(
          masked_question="how many orders?",
          tools_used="sql_query",
          latency=1.0,
          input_tokens=100,
          output_tokens=50,
          estimated_cost=0.001,
          success=True,
          is_fallback=False,
      ),
      RequestLog(
          masked_question="convert 100 usd to eur",
          tools_used="currency_convert",
          latency=2.0,
          input_tokens=200,
          output_tokens=40,
          estimated_cost=0.002,
          success=True,
          is_fallback=False,
      ),
      RequestLog(
          masked_question="unknown question",
          tools_used="",
          latency=0.5,
          input_tokens=50,
          output_tokens=10,
          estimated_cost=0.0,
          success=False,
          error_type="rate_limit",
          is_not_found=True,
      ),
      RequestLog(
          masked_question="unknown question",
          tools_used="",
          latency=0.5,
          input_tokens=50,
          output_tokens=10,
          estimated_cost=0.0,
          success=False,
          error_type="http_error",
          is_not_found=True,
      ),
  ]
  db.add_all(logs)
  db.commit()

  res = calculate_metrics(db)
  assert res["total_requests"] == 4
  assert res["average_latency"] == 1.0
  assert round(res["total_estimated_cost"], 3) == 0.003
  assert res["failure_rate"] == 0.5
  assert res["rate_limit_hit_count"] == 1
  assert len(res["most_common_failed_questions"]) == 1
  assert res["most_common_failed_questions"][0]["question"] == "unknown question"
  assert res["most_common_failed_questions"][0]["count"] == 2


def test_cost_calculation():
  in_tokens = 2000
  out_tokens = 1000

  # free tier default zero rates
  cost_free = (in_tokens / 1000.0) * 0.0 + (out_tokens / 1000.0) * 0.0
  assert cost_free == 0.0

  # cost calculation based on input and output token rates per 1k
  in_rate = 0.00015
  out_rate = 0.0006
  cost_paid = (in_tokens / 1000.0) * in_rate + (out_tokens / 1000.0) * out_rate
  assert round(cost_paid, 5) == 0.0009
