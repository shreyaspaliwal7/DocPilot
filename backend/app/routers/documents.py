from app.config import settings
from app.db.database import get_db
from app.db.models import Document, DocumentChunk
from app.services.embeddings import get_batch_embeddings
from app.services.ingest import chunk_pages, extract_pages
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
  filename = file.filename or "unknown"
  lower = filename.lower()
  if not (lower.endswith(".pdf") or lower.endswith(".txt")):
    raise HTTPException(
        status_code=400, detail="only .pdf and .txt files are supported"
    )

  content = await file.read()
  max_bytes = settings.max_file_size_mb * 1024 * 1024
  if len(content) > max_bytes:
    raise HTTPException(
        status_code=413, detail=f"file exceeds {settings.max_file_size_mb}mb limit"
    )

  pages = extract_pages(filename, content)
  if not pages:
    raise HTTPException(
        status_code=400, detail="no readable text found in document"
    )

  chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
  if not chunks:
    raise HTTPException(
        status_code=400, detail="could not generate chunks from document"
    )

  texts = [c["content"] for c in chunks]
  vectors = await get_batch_embeddings(texts)

  doc = Document(
      filename=filename, file_size=len(content), chunk_count=len(chunks)
  )
  db.add(doc)
  db.flush()

  for c, vec in zip(chunks, vectors):
    db_chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=c["chunk_index"],
        page_number=c["page_number"],
        content=c["content"],
        embedding=vec,
    )
    db.add(db_chunk)

  db.commit()
  db.refresh(doc)

  return {
      "id": doc.id,
      "filename": doc.filename,
      "chunk_count": doc.chunk_count,
      "message": "document uploaded and indexed successfully",
  }


@router.get("")
def list_documents(db: Session = Depends(get_db)):
  docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
  return [
      {
          "id": d.id,
          "filename": d.filename,
          "file_size": d.file_size,
          "chunk_count": d.chunk_count,
          "uploaded_at": d.uploaded_at.isoformat(),
      }
      for d in docs
  ]


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
  doc = db.query(Document).filter(Document.id == doc_id).first()
  if not doc:
    raise HTTPException(status_code=404, detail="document not found")

  db.delete(doc)
  db.commit()
  return {"message": "document deleted successfully"}
