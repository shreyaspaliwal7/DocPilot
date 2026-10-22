import asyncio
import random
import time
from app.config import settings
from fastapi import HTTPException
import httpx

_last_request_time = 0.0
_throttle_lock = asyncio.Lock()
_query_cache: dict[str, list[float]] = {}


async def _throttle():
  global _last_request_time
  # space requests to respect per-minute free tier limits
  async with _throttle_lock:
    interval = 60.0 / max(1, settings.requests_per_minute)
    elapsed = time.time() - _last_request_time
    if elapsed < interval:
      await asyncio.sleep(interval - elapsed)
    _last_request_time = time.time()


async def post_with_retry(
    url: str, payload: dict, timeout: float = 30.0
) -> dict:
  if not settings.gemini_api_key:
    raise HTTPException(
        status_code=500, detail="gemini_api_key is not set in environment"
    )

  for attempt in range(settings.max_retries + 1):
    await _throttle()
    try:
      async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)

        if resp.status_code == 200:
          return resp.json()

        # retry with exponential backoff on rate limit or temporary server errors
        if resp.status_code in (429, 503) and attempt < settings.max_retries:
          retry_after = resp.headers.get("retry-after")
          wait = (
              float(retry_after)
              if retry_after and retry_after.isdigit()
              else (2**attempt) + random.uniform(0.1, 0.5)
          )
          await asyncio.sleep(wait)
          continue

        if resp.status_code == 429:
          raise HTTPException(status_code=429, detail="gemini request limit reached")
        if resp.status_code == 503:
          raise HTTPException(status_code=503, detail="gemini service temporarily unavailable")

        resp.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException):
      # retry with exponential backoff on rate limit or temporary server errors
      if attempt < settings.max_retries:
        await asyncio.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
        continue
      raise HTTPException(status_code=503, detail="could not connect to gemini service")

  raise HTTPException(status_code=429, detail="gemini request limit reached")


async def _embed_single(text: str) -> list[float]:
  model = settings.gemini_embed_model.removeprefix("models/")
  url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={settings.gemini_api_key}"
  payload = {
      "model": f"models/{model}",
      "content": {"parts": [{"text": text}]},
      "outputDimensionality": settings.embedding_dim,
  }
  data = await post_with_retry(url, payload)
  vals = data.get("embedding", {}).get("values", [])
  if len(vals) > settings.embedding_dim:
    vals = vals[: settings.embedding_dim]
  elif len(vals) < settings.embedding_dim:
    vals = vals + [0.0] * (settings.embedding_dim - len(vals))
  return vals


async def get_query_embedding(query: str) -> list[float]:
  key = query.strip().lower()
  if key in _query_cache:
    return _query_cache[key]

  vector = await _embed_single(query)
  _query_cache[key] = vector
  return vector


async def get_batch_embeddings(texts: list[str]) -> list[list[float]]:
  if not texts:
    return []

  model = settings.gemini_embed_model.removeprefix("models/")
  url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents?key={settings.gemini_api_key}"

  all_embeddings = []
  batch_size = max(1, settings.batch_embed_size)

  for i in range(0, len(texts), batch_size):
    batch = texts[i : i + batch_size]
    reqs = [
        {
            "model": f"models/{model}",
            "content": {"parts": [{"text": t}]},
            "outputDimensionality": settings.embedding_dim,
        }
        for t in batch
    ]
    data = await post_with_retry(url, {"requests": reqs})
    raw_list = data.get("embeddings", [])
    for item in raw_list:
      vals = item.get("values", [])
      if len(vals) > settings.embedding_dim:
        vals = vals[: settings.embedding_dim]
      elif len(vals) < settings.embedding_dim:
        vals = vals + [0.0] * (settings.embedding_dim - len(vals))
      all_embeddings.append(vals)

  return all_embeddings
