from uuid import UUID

from fastapi import HTTPException, status

from backend.database.models import User, UserRole


def ensure_role(user: User, *allowed_roles: UserRole) -> None:
    """Enforce the backend role boundary independently of frontend route visibility."""

    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )


def ensure_owner(user: User, owner_id: UUID) -> None:
    """Reject access when an authenticated user does not own a private resource."""

    if user.id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
