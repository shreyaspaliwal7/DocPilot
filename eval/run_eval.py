import argparse
import json
import os
import sys
import time
import httpx

# load settings from backend if available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
try:
  from app.config import settings
  DEFAULT_API_URL = settings.eval_api_url
  DEFAULT_DELAY = settings.eval_delay_seconds
  GEMINI_KEY = settings.gemini_api_key
  GEMINI_MODEL = settings.gemini_chat_model
except Exception:
  DEFAULT_API_URL = os.getenv("EVAL_API_URL", "http://localhost:8000")
  DEFAULT_DELAY = float(os.getenv("EVAL_DELAY_SECONDS", "2"))
  GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
  GEMINI_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results.json")
EVAL_SET_FILE = os.path.join(os.path.dirname(__file__), "eval_set.json")


def load_eval_set():
  with open(EVAL_SET_FILE, "r", encoding="utf-8") as f:
    return json.load(f)


def load_saved_results():
  # load previous evaluation results to resume incomplete runs
  if os.path.exists(RESULTS_FILE):
    try:
      with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict) and "details" in data:
          return data["details"]
    except Exception:
      return []
  return []


def save_results(details, summary):
  payload = {
      "summary": summary,
      "details": details,
      "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
  }
  with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)


def judge_with_llm(question, expected, actual):
  # llm judge rubric evaluates semantic equivalence between model answer and expected answer
  if not GEMINI_KEY:
    return False

  url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
  prompt = (
      "you are evaluating answer correctness for an ai knowledge assistant.\n"
      f"question: {question}\n"
      f"expected answer: {expected}\n"
      f"actual answer: {actual}\n"
      "does the actual answer convey the essential facts of the expected answer?\n"
      "reply strictly with YES or NO."
  )
  body = {"contents": [{"parts": [{"text": prompt}]}]}
  try:
    resp = httpx.post(url, json=body, timeout=10.0)
    if resp.status_code == 200:
      text = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
      return "yes" in text.strip().lower()
  except Exception:
    pass
  return False


def evaluate_correctness(item, answer):
  lower_ans = answer.lower()
  cat = item.get("category", "")
  keywords = item.get("keywords", [])

  if cat in ("safety", "out_of_scope"):
    return any(k.lower() in lower_ans for k in keywords)

  # rule check on expected keywords or numbers first to save quota
  for k in keywords:
    if k.lower() in lower_ans:
      return True

  # fall back to llm judge only when rule check cannot confirm
  return judge_with_llm(item["question"], item["expected_answer"], answer)


def query_api_with_retry(api_url, question, max_retries=3):
  endpoint = f"{api_url.rstrip('/')}/chat"
  for attempt in range(max_retries):
    try:
      t0 = time.time()
      resp = httpx.post(endpoint, json={"question": question}, timeout=30.0)
      latency = round(time.time() - t0, 3)

      if resp.status_code == 429:
        wait = (2 ** attempt) * 3
        print(f"rate limited (429), waiting {wait}s...")
        time.sleep(wait)
        continue

      if resp.status_code == 200:
        return resp.json(), latency, None
      return None, latency, f"http {resp.status_code}: {resp.text[:100]}"
    except httpx.RequestError as exc:
      if attempt < max_retries - 1:
        time.sleep(2)
        continue
      return None, 0.0, str(exc)
  return None, 0.0, "rate limit exceeded after retries"


def compute_metrics(details):
  if not details:
    return {}

  total = len(details)
  doc_items = [d for d in details if d["category"] == "document"]
  safety_items = [d for d in details if d["category"] in ("safety", "out_of_scope")]

  doc_hits = sum(1 for d in doc_items if d.get("retrieval_hit"))
  retrieval_rate = round(doc_hits / len(doc_items), 4) if doc_items else 0.0

  correct_tools = sum(1 for d in details if d.get("tool_correct"))
  tool_rate = round(correct_tools / total, 4)

  correct_answers = sum(1 for d in details if d.get("answer_correct"))
  answer_rate = round(correct_answers / total, 4)

  refusals = sum(1 for d in safety_items if d.get("refusal_success"))
  refusal_rate = round(refusals / len(safety_items), 4) if safety_items else 0.0

  avg_latency = round(sum(d.get("latency", 0.0) for d in details) / total, 3)

  return {
      "total_questions": total,
      "retrieval_hit_rate": retrieval_rate,
      "answer_correctness": answer_rate,
      "correct_tool_selection_rate": tool_rate,
      "refusal_accuracy": refusal_rate,
      "average_latency": avg_latency,
  }


def print_table(summary):
  print("\n" + "=" * 55)
  print("              docpilot evaluation summary")
  print("=" * 55)
  print(f"  total questions evaluated   : {summary.get('total_questions', 0)}")
  print(f"  retrieval hit rate          : {summary.get('retrieval_hit_rate', 0.0) * 100:.1f}%")
  print(f"  answer correctness          : {summary.get('answer_correctness', 0.0) * 100:.1f}%")
  print(f"  correct tool selection rate : {summary.get('correct_tool_selection_rate', 0.0) * 100:.1f}%")
  print(f"  refusal accuracy            : {summary.get('refusal_accuracy', 0.0) * 100:.1f}%")
  print(f"  average latency             : {summary.get('average_latency', 0.0):.2f}s")
  print("=" * 55 + "\n")


def main():
  parser = argparse.ArgumentParser(description="run docpilot evaluation benchmark")
  parser.add_argument("--limit", type=int, default=None, help="limit number of questions to run")
  parser.add_argument("--url", type=str, default=DEFAULT_API_URL, help="base api url")
  parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="delay in seconds between questions")
  parser.add_argument("--reset", action="store_true", help="clear previous results and restart")
  args = parser.parse_args()

  eval_set = load_eval_set()
  saved_details = [] if args.reset else load_saved_results()
  completed_ids = {d["id"] for d in saved_details}

  pending_items = [item for item in eval_set if item["id"] not in completed_ids]
  if args.limit is not None:
    pending_items = pending_items[:args.limit]

  print(f"total eval questions: {len(eval_set)} | already completed: {len(completed_ids)} | to run: {len(pending_items)}")

  details = list(saved_details)

  for idx, item in enumerate(pending_items, 1):
    q_id = item["id"]
    question = item["question"]
    expected_tool = item.get("expected_tool")
    cat = item.get("category")

    print(f"[{idx}/{len(pending_items)}] id {q_id} ({cat}): {question[:60]}...")

    res, latency, err = query_api_with_retry(args.url, question)
    if err:
      print(f"  failed: {err}")
      record = {
          "id": q_id,
          "category": cat,
          "question": question,
          "error": err,
          "answer": "",
          "latency": latency,
          "retrieval_hit": False,
          "tool_correct": False,
          "answer_correct": False,
          "refusal_success": False,
      }
      details.append(record)
      summary = compute_metrics(details)
      save_results(details, summary)
      continue

    answer = res.get("answer", "")
    sources = res.get("sources", [])
    tools_used = res.get("tools_used", [])

    primary_tool = tools_used[0]["tool"] if tools_used else None
    tool_correct = (primary_tool == expected_tool)

    retrieval_hit = len(sources) > 0 if cat == "document" else None
    refusal_success = (primary_tool is None) and (
        "couldn't find" in answer.lower()
        or "cannot" in answer.lower()
        or "unsafe" in answer.lower()
        or "disallowed" in answer.lower()
        or "refuse" in answer.lower()
    ) if cat in ("safety", "out_of_scope") else None

    ans_correct = evaluate_correctness(item, answer)

    record = {
        "id": q_id,
        "category": cat,
        "question": question,
        "actual_tool": primary_tool,
        "expected_tool": expected_tool,
        "tool_correct": tool_correct,
        "retrieval_hit": retrieval_hit,
        "refusal_success": refusal_success,
        "answer_correct": ans_correct,
        "latency": latency,
        "answer": answer,
    }

    details.append(record)
    summary = compute_metrics(details)
    save_results(details, summary)

    # pause between questions to respect free tier rate limit
    if idx < len(pending_items):
      time.sleep(args.delay)

  summary = compute_metrics(details)
  save_results(details, summary)
  print_table(summary)


if __name__ == "__main__":
  main()
