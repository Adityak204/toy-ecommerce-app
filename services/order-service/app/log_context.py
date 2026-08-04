"""
Request context management using contextvars

This module provides functions to get/set the correlation id for the
current request. The correlation id is stored in a context variable, 
which means each concurrent request will have its own correlation id.
"""

import uuid
from contextvars import ContextVar
from typing import Optional


# Create a context variable to store the correlation id
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """
    Get the correlation id for the current request

    This function retrieves the correlation id from the context variable
    If no correlation id is set, it returns None

    Returns:
        The correlation id for the current request
    """
    return correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation id for the current request

    This function sets the correlation id in the context variable
    All subsequent calls to get_correlation_id() in the same context
    will return the same value

    Args:
        correlation_id: The correlation id for the current request
    """
    correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """
    Generate a new correlation id for the current request

    This function generates a new correlation id for the current request
    Use this when no correlation id is provided by the client.

    Returns:
        The new correlation id for the current request
    """
    return str(uuid.uuid4())