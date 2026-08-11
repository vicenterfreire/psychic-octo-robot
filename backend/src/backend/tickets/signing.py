import base64
import hashlib
import hmac
from uuid import UUID

TOKEN_VERSION = "v1"
MINIMUM_SECRET_BYTES = 32


class InvalidTicketSigningSecretError(ValueError):
    """The configured signing secret is absent or too short."""


class TicketSigner:
    def __init__(self, secret: str) -> None:
        secret_bytes = secret.encode("utf-8")
        if len(secret_bytes) < MINIMUM_SECRET_BYTES:
            raise InvalidTicketSigningSecretError(
                f"Ticket signing secret must contain at least {MINIMUM_SECRET_BYTES} bytes."
            )
        self._secret = secret_bytes

    def sign(self, ticket_id: UUID) -> str:
        identifier = ticket_id.hex
        signature = self._signature(identifier)
        return f"{TOKEN_VERSION}.{identifier}.{signature}"

    def verify(self, token: str) -> UUID | None:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        version, identifier, provided_signature = parts
        if version != TOKEN_VERSION or len(identifier) != 32:
            return None
        try:
            ticket_id = UUID(hex=identifier)
        except ValueError:
            return None
        if identifier != ticket_id.hex:
            return None
        expected_signature = self._signature(identifier)
        if not hmac.compare_digest(provided_signature, expected_signature):
            return None
        return ticket_id

    def _signature(self, identifier: str) -> str:
        payload = f"{TOKEN_VERSION}:{identifier}".encode()
        digest = hmac.new(self._secret, payload, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
