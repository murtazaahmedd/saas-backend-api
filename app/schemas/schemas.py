"""Request and response models. Validation lives in field constraints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "member", "viewer"]
Status = Literal["active", "paused", "done"]


class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class SignupResponse(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: Role
    access_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class InviteUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Role = "member"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: Role
    created_at: datetime


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field("", max_length=2000)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[Status] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: Status
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ProjectPage(BaseModel):
    items: List[ProjectResponse]
    next_cursor: Optional[str]
