from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ImportLog, Place
from app.schemas import DashboardRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db)):
    active = db.query(Place).filter(Place.is_active.is_(True)).count()
    inactive = db.query(Place).filter(Place.is_active.is_(False)).count()
    rows = (
        db.query(Place.category, func.count(Place.id))
        .filter(Place.is_active.is_(True))
        .group_by(Place.category)
        .all()
    )
    last_import = db.query(ImportLog).order_by(ImportLog.started_at.desc()).first()
    return {
        "active_places": active,
        "inactive_places": inactive,
        "categories": {category: count for category, count in rows},
        "last_import": last_import,
    }
