from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from backend.database.models import Reservation, ReservationStatus


class PaymentOutcome(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"


class ReservationCreate(BaseModel):
    event_id: UUID = Field(description="Published event receiving the temporary inventory hold.")
    quantity: int = Field(
        gt=0,
        le=1_000_000,
        description="General-admission ticket quantity to hold.",
        examples=[2],
    )


class PaymentCommand(BaseModel):
    outcome: PaymentOutcome = Field(
        description="Deterministic simulation result; no financial data is collected.",
        examples=[PaymentOutcome.APPROVED],
    )


class ReservationResponse(BaseModel):
    id: UUID
    event_id: UUID
    quantity: int
    status: ReservationStatus
    created_at: datetime
    expires_at: datetime
    server_time: datetime
    ticket_count: int

    @classmethod
    def from_model(
        cls,
        reservation: Reservation,
        server_time: datetime,
        ticket_count: int = 0,
    ) -> Self:
        return cls(
            id=reservation.id,
            event_id=reservation.event_id,
            quantity=reservation.quantity,
            status=reservation.status,
            created_at=reservation.created_at,
            expires_at=reservation.expires_at,
            server_time=server_time,
            ticket_count=ticket_count,
        )
