import time
from app.config import settings
from app.db.database import get_db
from app.db.models import RequestLog
from app.guardrails.pii import mask_pii
from app.guardrails.safety import check_request_safety
from app.services.router import process_chat
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class ChatRequest(BaseModel):
  question: str


class SourceItem(BaseModel):
  document: str
  page: int
  snippet: str
  score: float


class ToolUsedItem(BaseModel):
  tool: str
  input: str
  output_summary: str


class ChatResponse(BaseModel):
  answer: str
  sources: list[SourceItem] = []
  tools_used: list[ToolUsedItem] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
  start_time = time.time()
  raw_q = req.question.strip()
  if not raw_q:
    log_entry = RequestLog(
        masked_question="",
        tools_used="",
        latency=round(time.time() - start_time, 3),
        input_tokens=0,
        output_tokens=0,
        estimated_cost=0.0,
        success=True,
        is_fallback=False,
        is_not_found=True,
    )
    db.add(log_entry)
    db.commit()
    return ChatResponse(
        answer="i couldn't find this in the provided documents",
        sources=[],
        tools_used=[],
    )

  masked_q = mask_pii(raw_q)
  safe, refusal = check_request_safety(raw_q)
  if not safe:
    log_entry = RequestLog(
        masked_question=masked_q,
        tools_used="",
        latency=round(time.time() - start_time, 3),
        input_tokens=0,
        output_tokens=0,
        estimated_cost=0.0,
        success=True,
        is_fallback=False,
        is_not_found=False,
    )
    db.add(log_entry)
    db.commit()
    return ChatResponse(answer=refusal, sources=[], tools_used=[])

  try:
    answer, sources, tools_used, meta = await process_chat(masked_q, db)
    latency = round(time.time() - start_time, 3)
    in_tokens = meta.get("input_tokens", 0)
    out_tokens = meta.get("output_tokens", 0)
    # cost calculation based on input and output token rates per 1k
    cost = (in_tokens / 1000.0) * settings.cost_per_1k_input + (
        out_tokens / 1000.0
    ) * settings.cost_per_1k_output
    tools_str = ",".join(t["tool"] for t in tools_used)
    is_not_found = (
        "couldn't find this" in answer.lower()
        or "could not determine a response" in answer.lower()
    )

    log_entry = RequestLog(
        masked_question=masked_q,
        tools_used=tools_str,
        latency=latency,
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        estimated_cost=round(cost, 6),
        success=True,
        is_fallback=meta.get("is_fallback", False),
        is_not_found=is_not_found,
    )
    db.add(log_entry)
    db.commit()

    return ChatResponse(
        answer=mask_pii(answer),
        sources=[SourceItem(**s) for s in sources],
        tools_used=[ToolUsedItem(**t) for t in tools_used],
    )
  except HTTPException as exc:
    latency = round(time.time() - start_time, 3)
    err_type = "rate_limit" if exc.status_code == 429 else "http_error"
    log_entry = RequestLog(
        masked_question=masked_q,
        tools_used="",
        latency=latency,
        input_tokens=0,
        output_tokens=0,
        estimated_cost=0.0,
        success=False,
        is_fallback=False,
        error_type=err_type,
        is_not_found=False,
    )
    db.add(log_entry)
    db.commit()
    raise exc
  except Exception as exc:
    latency = round(time.time() - start_time, 3)
    log_entry = RequestLog(
        masked_question=masked_q,
        tools_used="",
        latency=latency,
        input_tokens=0,
        output_tokens=0,
        estimated_cost=0.0,
        success=False,
        is_fallback=False,
        error_type="server_error",
        is_not_found=False,
    )
    db.add(log_entry)
    db.commit()
    raise exc
