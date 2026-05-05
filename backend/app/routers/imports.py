from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_import_token
from app.db import get_db
from app.models import ImportLog
from app.schemas import ImportLogRead
from app.services.importer import PlaceImporter

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/run", response_model=ImportLogRead)
def run_import(_: None = Depends(require_import_token), db: Session = Depends(get_db)):
    return PlaceImporter(db).run()


@router.get("/logs", response_model=list[ImportLogRead])
def list_import_logs(db: Session = Depends(get_db)):
    return db.query(ImportLog).order_by(ImportLog.started_at.desc()).limit(20).all()
