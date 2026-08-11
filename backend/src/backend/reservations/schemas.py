from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from backend.database.models import Reservation, ReservationStatus


class ReservationCreate(BaseModel):
    event_id: UUID
    quantity: int = Field(gt=0, le=1_000_000)


class ReservationResponse(BaseModel):
    id: UUID
    event_id: UUID
    quantity: int
    status: ReservationStatus
    created_at: datetime
    expires_at: datetime
    server_time: datetime

    @classmethod
    def from_model(cls, reservation: Reservation, server_time: datetime) -> Self:
        return cls(
            id=reservation.id,
            event_id=reservation.event_id,
            quantity=reservation.quantity,
            status=reservation.status,
            created_at=reservation.created_at,
            expires_at=reservation.expires_at,
            server_time=server_time,
        )
