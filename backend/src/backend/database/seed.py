from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from backend.database.engine import get_engine
from backend.database.models import (
    CatalogProvider,
    CatalogSnapshot,
    Event,
    EventStatus,
    User,
    UserRole,
)

ORGANIZER_ID = UUID("11111111-1111-4111-8111-111111111111")
CUSTOMER_ONE_ID = UUID("22222222-2222-4222-8222-222222222221")
CUSTOMER_TWO_ID = UUID("22222222-2222-4222-8222-222222222222")
GATE_ID = UUID("33333333-3333-4333-8333-333333333333")
CATALOG_SNAPSHOT_ID = UUID("44444444-4444-4444-8444-444444444444")
EVENT_ID = UUID("55555555-5555-4555-8555-555555555555")


@dataclass(frozen=True, slots=True)
class SeedUser:
    id: UUID
    email: str
    password: str
    role: UserRole


SEED_USERS = (
    SeedUser(ORGANIZER_ID, "organizer@example.com", "Organizer123!", UserRole.ORGANIZER),
    SeedUser(CUSTOMER_ONE_ID, "customer.one@example.com", "Customer123!", UserRole.CUSTOMER),
    SeedUser(CUSTOMER_TWO_ID, "customer.two@example.com", "Customer123!", UserRole.CUSTOMER),
    SeedUser(GATE_ID, "gate@example.com", "Gate123!", UserRole.GATE),
)


def seed_database() -> dict[str, int]:
    inserted = {"users": 0, "catalog_snapshots": 0, "events": 0}
    password_hash = PasswordHash.recommended()

    with Session(get_engine()) as session, session.begin():
        for seed_user in SEED_USERS:
            if session.get(User, seed_user.id) is None:
                session.add(
                    User(
                        id=seed_user.id,
                        email=seed_user.email,
                        password_hash=password_hash.hash(seed_user.password),
                        role=seed_user.role,
                    )
                )
                inserted["users"] += 1

        if session.get(CatalogSnapshot, CATALOG_SNAPSHOT_ID) is None:
            session.add(
                CatalogSnapshot(
                    id=CATALOG_SNAPSHOT_ID,
                    provider=CatalogProvider.TICKETMASTER,
                    provider_event_id="seed-aurora-live-2030",
                    name="Aurora Live 2030",
                    description="Stable Ticketmaster-style source data for the evaluation flow.",
                    image_url=None,
                    source_url="https://example.com/events/aurora-live-2030",
                    raw_data={
                        "id": "seed-aurora-live-2030",
                        "name": "Aurora Live 2030",
                        "classifications": [{"segment": {"name": "Music"}}],
                    },
                )
            )
            inserted["catalog_snapshots"] += 1

        if session.get(Event, EVENT_ID) is None:
            session.add(
                Event(
                    id=EVENT_ID,
                    organizer_id=ORGANIZER_ID,
                    catalog_snapshot_id=CATALOG_SNAPSHOT_ID,
                    name="Aurora Live 2030",
                    description="A seeded published event ready for the customer flow.",
                    venue_name="Gather Hall",
                    address="100 Avenida das Artes",
                    city="Sao Paulo",
                    country_code="BR",
                    start_at=datetime(2030, 9, 21, 22, 0, tzinfo=UTC),
                    capacity=100,
                    price_minor=15000,
                    currency="BRL",
                    status=EventStatus.PUBLISHED,
                )
            )
            inserted["events"] += 1

    return inserted


def main() -> None:
    inserted = seed_database()
    print(
        "Seed completed: "
        f"{inserted['users']} users, "
        f"{inserted['catalog_snapshots']} catalog snapshots, "
        f"{inserted['events']} events inserted."
    )


if __name__ == "__main__":
    main()
