from datetime import datetime
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str


class CompanyUpdate(BaseModel):
    name: str | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
