from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
import logging

from app.models import UserCreate, UserResponse, Token
from app.database import create_user, get_user_by_email
from app.security import hash_password, verify_password, create_access_token, get_jwks
from app.logging_config import setup_logging
# from app.middleware.logging_middleware import LoggingMiddleware

# COnfigure logging
# setup_logging() # TODO: Fix logging

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="1.0.0")

# Add logging middleware
# app.add_middleware(LoggingMiddleware) # TODO: Fix logging


@app.on_event("startup")
async def startup_event():
    logger.info(
        "Service started successfully.",
        extra={"event": "service_startup", "status": "success"}
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
    }


@app.post("/register", response_model=UserResponse, status_code=201)
async def register(user_create: UserCreate):
    """Register a new user."""
    if get_user_by_email(user_create.email):
        logger.warning(
            "Registration failed - email already exists.",
            extra={
                "event": "registeration_failed",
                "email": user_create.email,
                "reason": "email_already_exists",
            }
        )
        raise HTTPException(
            status_code=409,
            detail="Registration failed - email already exists.",
        )
    hashed_password = hash_password(user_create.password)
    user = create_user(user_create.email, hashed_password)

    logger.info(
        "User registered successfully.",
        extra={
            "event": "user_registered",
            "email": user_create.email,
            "user_id": user.id,
        }
    )

    return UserResponse(id=user.id, email=user.email)


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and issue a JWT access token."""
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(
            "Login failed - invalid credentials.",
            extra={
                "event": "login_failed",
                "email": form_data.username,
                "reason": "invalid_credentials",
            }
        )
        raise HTTPException(
            status_code=401,
            detail="Login failed - invalid credentials.",
        )
    access_token = create_access_token(user.id)

    logger.info(
        "User logged in successfully.",
        extra={
            "event": "user_logged_in",
            "email": form_data.username,
            "user_id": user.id,
        }
    )

    return Token(access_token=access_token)


@app.get("/.well-known/jwks.json")
async def jwks():
    """Publish the public keys used to verify the JWT access tokens, in the JWKS format."""
    return get_jwks()