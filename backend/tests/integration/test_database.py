from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.passwords import verify_password
from backend.database.engine import get_engine
from backend.database.models import Event, EventStatus, User, UserRole
from backend.database.seed import CUSTOMER_ONE_ID, EVENT_ID, ORGANIZER_ID, seed_database

pytestmark = pytest.mark.integration


def test_seeded_evaluation_data_is_ready() -> None:
    with Session(get_engine()) as session:
        users = session.scalars(select(User).order_by(User.email)).all()
        event = session.get(Event, EVENT_ID)
        organizer = session.get(User, ORGANIZER_ID)

    assert [user.role for user in users] == [
        UserRole.CUSTOMER,
        UserRole.CUSTOMER,
        UserRole.GATE,
        UserRole.ORGANIZER,
    ]
    assert organizer is not None
    assert verify_password("Organizer123!", organizer.password_hash)
    assert event is not None
    assert event.status is EventStatus.PUBLISHED
    assert event.capacity == 100
    assert event.price_minor == 15000


def test_seed_is_idempotent() -> None:
    assert seed_database() == {"users": 0, "catalog_snapshots": 0, "events": 0}


def test_database_rejects_nonpositive_reservation_quantity() -> None:
    connection = get_engine().connect()
    transaction = connection.begin()

    try:
        with pytest.raises(IntegrityError, match="ck_reservations_positive_quantity"):
            connection.execute(
                text(
                    """
                    INSERT INTO reservations (
                        id,
                        customer_id,
                        event_id,
                        quantity,
                        status,
                        expires_at
                    )
                    VALUES (
                        :reservation_id,
                        :customer_id,
                        :event_id,
                        0,
                        'pending',
                        now() + interval '10 minutes'
                    )
                    """
                ),
                {
                    "reservation_id": uuid4(),
                    "customer_id": CUSTOMER_ONE_ID,
                    "event_id": EVENT_ID,
                },
            )
    finally:
        transaction.rollback()
        connection.close()
