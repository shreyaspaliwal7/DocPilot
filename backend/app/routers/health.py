from app.db.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
  try:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
  except Exception as exc:
    return {"status": "error", "database": str(exc)}
