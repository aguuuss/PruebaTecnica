from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceBase(BaseModel):
    name: str
    address: str | None = None
    city: str | None = None
    category: str = "bar"
    source: str = "manual"
    source_url: str | None = None
    contact: str | None = None
    opening_hours: str | None = None
    services: str | None = None
    description: str | None = None
    is_active: bool = True


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    category: str | None = None
    contact: str | None = None
    opening_hours: str | None = None
    services: str | None = None
    description: str | None = None
    is_active: bool | None = None


class PlaceRead(PlaceBase):
    id: int
    normalized_name: str
    normalized_address: str | None = None
    source_url: str
    fetched_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportLogRead(BaseModel):
    id: int
    source: str
    status: str
    items_found: int
    created_count: int
    updated_count: int
    duplicate_count: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DashboardRead(BaseModel):
    active_places: int
    inactive_places: int
    categories: dict[str, int]
    last_import: ImportLogRead | None


class PlaceResetResponse(BaseModel):
    status: str
    deleted_places: int
    deleted_logs: int
