from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models import ImportLog
from app.schemas import ImportLogRead
from app.services.importer import PlaceImporter

router = APIRouter(prefix="/imports", tags=["imports"])


def require_import_token(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().import_run_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Import token is not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    provided = authorization.removeprefix("Bearer ").strip()
    if not provided or not compare_digest(provided, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )


@router.post("/run", response_model=ImportLogRead)
def run_import(_: None = Depends(require_import_token), db: Session = Depends(get_db)):
    return PlaceImporter(db).run()


@router.get("/logs", response_model=list[ImportLogRead])
def list_import_logs(db: Session = Depends(get_db)):
    return db.query(ImportLog).order_by(ImportLog.started_at.desc()).limit(20).all()
