from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Place
from app.schemas import PlaceCreate, PlaceRead, PlaceUpdate
from app.services.normalization import normalize_text

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", response_model=list[PlaceRead])
def list_places(
    q: str | None = None,
    active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Place)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Place.name.ilike(like), Place.address.ilike(like), Place.city.ilike(like)))
    if active is not None:
        query = query.filter(Place.is_active == active)
    return query.order_by(Place.updated_at.desc()).all()


@router.post("", response_model=PlaceRead)
def create_place(payload: PlaceCreate, db: Session = Depends(get_db)):
    place = Place(
        **payload.model_dump(exclude={"source_url"}),
        normalized_name=normalize_text(payload.name, remove_fillers=True),
        normalized_address=normalize_text(payload.address),
        source_url=payload.source_url or "manual",
    )
    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@router.patch("/{place_id}", response_model=PlaceRead)
def update_place(place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    place = db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(place, key, value)
    if "name" in data:
        place.normalized_name = normalize_text(place.name, remove_fillers=True)
    if "address" in data:
        place.normalized_address = normalize_text(place.address)

    db.commit()
    db.refresh(place)
    return place


@router.delete("/{place_id}", response_model=PlaceRead)
def deactivate_place(place_id: int, db: Session = Depends(get_db)):
    place = db.get(Place, place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    place.is_active = False
    db.commit()
    db.refresh(place)
    return place
