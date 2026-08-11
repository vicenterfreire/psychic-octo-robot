from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base


class UserRole(StrEnum):
    ORGANIZER = "organizer"
    CUSTOMER = "customer"
    GATE = "gate"


class CatalogProvider(StrEnum):
    TICKETMASTER = "ticketmaster"


class EventStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ReservationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    EXPIRED = "expired"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        CheckConstraint(
            "role IN ('organizer', 'customer', 'gate')",
            name="user_role",
        ),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_sessions_expiry_after_creation"),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at", name="ck_sessions_revocation"
        ),
        CheckConstraint("octet_length(token_digest) = 32", name="ck_sessions_digest_length"),
        UniqueConstraint("token_digest", name="uq_sessions_token_digest"),
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_digest: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CatalogSnapshot(Base):
    __tablename__ = "catalog_snapshots"
    __table_args__ = (
        CheckConstraint("provider IN ('ticketmaster')", name="catalog_provider"),
        Index("ix_catalog_snapshots_provider_event", "provider", "provider_event_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[CatalogProvider] = mapped_column(
        Enum(
            CatalogProvider,
            name="catalog_provider",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
    )
    provider_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_events_positive_capacity"),
        CheckConstraint("price_minor >= 0", name="ck_events_nonnegative_price"),
        CheckConstraint("status IN ('draft', 'published')", name="event_status"),
        CheckConstraint(
            "char_length(country_code) = 2 AND country_code = upper(country_code)",
            name="ck_events_country_code",
        ),
        CheckConstraint(
            "char_length(currency) = 3 AND currency = upper(currency)",
            name="ck_events_currency_code",
        ),
        Index("ix_events_organizer_id", "organizer_id"),
        Index("ix_events_status_start_at", "status", "start_at"),
        UniqueConstraint("catalog_snapshot_id", name="uq_events_catalog_snapshot_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organizer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    catalog_snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog_snapshots.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    venue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    status: Mapped[EventStatus] = mapped_column(
        Enum(
            EventStatus,
            name="event_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
        default=EventStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_reservations_positive_quantity"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'declined', 'expired')",
            name="reservation_status",
        ),
        CheckConstraint("expires_at > created_at", name="ck_reservations_expiry_after_creation"),
        Index("ix_reservations_customer_id", "customer_id"),
        Index("ix_reservations_event_status_expiry", "event_id", "status", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(
            ReservationStatus,
            name="reservation_status",
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda members: [member.value for member in members],
        ),
        nullable=False,
        default=ReservationStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("ticket_number > 0", name="ck_tickets_positive_number"),
        CheckConstraint(
            "(used_at IS NULL) = (used_by_user_id IS NULL)",
            name="ck_tickets_usage_fields_together",
        ),
        CheckConstraint("used_at IS NULL OR used_at >= issued_at", name="ck_tickets_usage_time"),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= issued_at", name="ck_tickets_revocation_time"
        ),
        UniqueConstraint("reservation_id", "ticket_number", name="uq_tickets_reservation_number"),
        Index("ix_tickets_reservation_id", "reservation_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    reservation_id: Mapped[UUID] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), nullable=False
    )
    ticket_number: Mapped[int] = mapped_column(Integer, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
