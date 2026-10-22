from app.config import settings
from app.services.embeddings import get_query_embedding
from app.services.retrieval import search_similar_chunks
from sqlalchemy.orm import Session


async def search_documents(query: str, db: Session) -> dict:
  query_vec = await get_query_embedding(query)
  chunks = search_similar_chunks(db, query_vec, settings.top_k)

  if not chunks:
    return {"chunks": [], "message": "no documents matched the query"}

  best_score = chunks[0]["score"]
  if best_score < settings.score_threshold:
    return {
        "chunks": [],
        "message": "best match is below similarity threshold",
    }

  return {
      "chunks": chunks,
      "message": f"found {len(chunks)} relevant document chunks",
  }
