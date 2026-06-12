"""Authentication request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload to create a new account."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    turnstile_token: str = ""


class LoginRequest(BaseModel):
    """Payload to authenticate with email + password."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    email_verified: bool


class RequestVerificationRequest(BaseModel):
    """Request a new verification email."""

    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Verify an email address with a one-time token."""

    token: str


class RequestPasswordResetRequest(BaseModel):
    """Request a password-reset email."""

    email: EmailStr
    turnstile_token: str = ""


class ResetPasswordRequest(BaseModel):
    """Complete a password reset with a one-time token."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password while authenticated."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
