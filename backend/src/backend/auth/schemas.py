from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.database.models import UserRole


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=320,
        description="Seeded account email. It is normalized to lowercase.",
        examples=["organizer@example.com"],
    )
    password: str = Field(
        min_length=1,
        max_length=1024,
        description="Plaintext password accepted only by the login boundary.",
        examples=["Organizer123!"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or any(character.isspace() for character in normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
