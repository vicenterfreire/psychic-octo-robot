from uuid import UUID, uuid4

import pytest

from backend.tickets.signing import InvalidTicketSigningSecretError, TicketSigner

TEST_SECRET = "ticket-signing-test-secret-value-32-bytes"


def test_ticket_token_is_deterministic_versioned_and_verifiable() -> None:
    signer = TicketSigner(TEST_SECRET)
    ticket_id = UUID("77777777-7777-4777-8777-777777777771")

    token = signer.sign(ticket_id)

    assert token == signer.sign(ticket_id)
    assert token.startswith(f"v1.{ticket_id.hex}.")
    assert signer.verify(token) == ticket_id
    assert "customer" not in token
    assert "@" not in token


def test_ticket_token_rejects_modified_or_unsupported_values() -> None:
    signer = TicketSigner(TEST_SECRET)
    token = signer.sign(uuid4())
    version, identifier, signature = token.split(".")
    changed_identifier = ("0" if identifier[0] != "0" else "1") + identifier[1:]
    changed_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")

    assert signer.verify(f"v2.{identifier}.{signature}") is None
    assert signer.verify(f"{version}.{changed_identifier}.{signature}") is None
    assert signer.verify(f"{version}.{identifier}.{changed_signature}") is None
    assert signer.verify("not-a-ticket") is None


def test_ticket_signing_requires_a_dedicated_high_entropy_secret() -> None:
    with pytest.raises(InvalidTicketSigningSecretError):
        TicketSigner("too-short")
