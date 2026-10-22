from app.config import settings
from app.services.embeddings import post_with_retry
from fastapi import HTTPException


async def call_gemini(
    contents: list[dict],
    system_instruction: str | None = None,
    tools: list[dict] | None = None,
) -> dict:
  payload = {
      "contents": contents,
      "generationConfig": {"temperature": 0.1},
  }
  if system_instruction:
    payload["system_instruction"] = {
        "parts": [{"text": system_instruction}]
    }
  if tools:
    payload["tools"] = tools

  models_to_try = [settings.gemini_chat_model, settings.gemini_fallback_model]

  for idx, model in enumerate(models_to_try):
    clean_model = model.removeprefix("models/")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={settings.gemini_api_key}"
    try:
      # fall back to secondary model when primary exhausts free tier rate limit
      data = await post_with_retry(url, payload)
      data["_used_fallback"] = idx > 0
      data["_model"] = model
      return data
    except HTTPException as exc:
      if exc.status_code == 429:
        if idx < len(models_to_try) - 1:
          continue
        raise HTTPException(
            status_code=429,
            detail=(
                "rate limit reached on both primary and fallback models, please"
                " try again later"
            ),
        )
      raise exc


async def generate_answer(question: str, chunks: list[dict]) -> str:
  context_parts = [
      f"[{c['document']} page {c['page']}]:\n{c['snippet']}" for c in chunks
  ]
  context = "\n\n".join(context_parts)

  prompt = (
      "you are a helpful assistant for docpilot.\n"
      "answer the question strictly using only the document excerpts below.\n"
      "if the answer cannot be found in the excerpts, reply exactly with: i"
      " couldn't find this in the provided documents\n\n"
      f"context:\n{context}\n\n"
      f"question: {question}\n\n"
      "answer:"
  )

  contents = [{"parts": [{"text": prompt}]}]
  data = await call_gemini(contents)
  candidates = data.get("candidates", [])
  if candidates:
    parts = candidates[0].get("content", {}).get("parts", [])
    if parts:
      return parts[0].get("text", "").strip()

  return "i couldn't find this in the provided documents"
