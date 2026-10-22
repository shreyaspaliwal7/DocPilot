from app.db.database import get_db
from app.services.metrics import calculate_metrics
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
  return calculate_metrics(db)
