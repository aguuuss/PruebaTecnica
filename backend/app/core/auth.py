from hmac import compare_digest

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


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
