from typing import Literal

from pydantic import BaseModel, Field


class CatalogEvent(BaseModel):
    provider: Literal["ticketmaster"] = "ticketmaster"
    provider_event_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    description: str | None
    image_url: str | None = Field(max_length=2048)
    source_url: str | None = Field(max_length=2048)


class CatalogSearchResponse(BaseModel):
    items: list[CatalogEvent]
