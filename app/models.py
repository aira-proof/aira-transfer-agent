from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class TransferStatus(str, Enum):
    authorized = "authorized"
    denied = "denied"
    pending_approval = "pending_approval"
    executed = "executed"
    failed = "failed"


class TransferRequest(BaseModel):
    recipient: str = Field(..., min_length=1, max_length=200)
    iban: str = Field(..., min_length=10, max_length=34)
    amount_eur: float = Field(..., gt=0)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")
    country: str = Field(..., min_length=2, max_length=2)
    purpose: str = Field(..., min_length=1, max_length=500)


class Transfer(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    request: TransferRequest
    status: TransferStatus
    action_uuid: str | None = None
    receipt_uuid: str | None = None
    verify_url: str | None = None
    signature: str | None = None
    denial_reason: str | None = None
    approval_url: str | None = None
    agent_reasoning: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = None
