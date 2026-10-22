from app.db.models import Document, DocumentChunk
from sqlalchemy.orm import Session


def search_similar_chunks(
    db: Session, query_vector: list[float], top_k: int
) -> list[dict]:
  distance_col = DocumentChunk.embedding.cosine_distance(query_vector).label(
      "distance"
  )
  results = (
      db.query(DocumentChunk, Document.filename, distance_col)
      .join(Document, DocumentChunk.document_id == Document.id)
      .order_by(distance_col.asc())
      .limit(top_k)
      .all()
  )

  chunks = []
  for chunk, filename, distance in results:
    # convert cosine distance to cosine similarity
    score = 1.0 - float(distance)
    chunks.append({
        "document": filename,
        "page": chunk.page_number,
        "snippet": chunk.content,
        "score": round(score, 4),
    })

  return chunks
