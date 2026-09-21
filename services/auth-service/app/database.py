from typing import Dict, Optional
import logging
from app.models import User

logger = logging.getLogger(__name__)

# In-memory database (dictionary), keyed by email
user_db: Dict[str, User] = {}

# Auto-incrementing ID counter
_next_id = 1


def get_user_by_email(email: str) -> Optional[User]:
    """Retrieve user by email."""
    user = user_db.get(email)
    logger.debug(
        "User lookup",
        extra={
            "event": "user_get",
            "email": email,
            "found": user is not None,
        },
    )
    return user


def create_user(email: str, hashed_password: str) -> User:
    """Create a new user."""
    global _next_id

    user = User(id=_next_id, email=email, hashed_password=hashed_password)
    user_db[email] = user
    logger.debug(
        "User created in database",
        extra={
            "event": "user_db_create",
            "email": email,
            "user_id": _next_id,
        },
    )
    _next_id += 1
    return user