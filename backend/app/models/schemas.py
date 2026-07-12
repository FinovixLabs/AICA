from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Any
import re

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict[str, Any]


# ── Clients ───────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    gstin: str
    name: str
    state: str | None = None
    type: str | None = None
    scheme: str | None = None

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        v = v.strip().upper()
        if not GSTIN_RE.match(v):
            raise ValueError("GSTIN format is invalid")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v


class ClientOut(BaseModel):
    gstin: str
    name: str
    state: str | None = None
    type: str | None = None
    scheme: str | None = None
    status: str | None = None
    init: str | None = None


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    name: str
    type: str
    route: str
    extracted: str
    status: str


# ── Filing ────────────────────────────────────────────────────────────────────

class PrerequisitesRequest(BaseModel):
    gstin: str
    filing_type: str


class RequirementsCheckRequest(BaseModel):
    gstin: str
    period: str | None = None


class FilingStartRequest(BaseModel):
    gstin: str
    period: str | None = None


class FilingEditRequest(BaseModel):
    gstin: str
    period: str | None = None
    instruction: str
    filing_csv: str
    filing_json: dict[str, Any]


class RegisterEditRequest(BaseModel):
    gstin: str
    period: str | None = None
    instruction: str
    beta_register: list[dict[str, Any]]


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []
    context: str = "filing"
    gstin: str | None = None
    filing_output: dict[str, Any] | None = None


# ── Notices ───────────────────────────────────────────────────────────────────

class ApproveReplyRequest(BaseModel):
    gstin: str
    noticeId: str
    html: str
    version: str
