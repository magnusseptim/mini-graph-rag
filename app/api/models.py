from __future__ import annotations
from typing import Literal
from datetime import datetime, timezone
from pydantic import BaseModel, StrictInt, StrictStr, Field, field_validator


class EchoRequest(BaseModel):
    message: StrictStr = Field(min_length=1, max_length=2000)
    repeat: StrictInt = Field(default=1, ge=1, le=5)
    mode: Literal["upper", "lower", "title"] = "upper"

    @field_validator("message")
    @classmethod
    def normalize_whitespace(cls, v: str) -> str:
        return " ".join(v.split())  # Normalize whitespace


class EchoResponse(BaseModel):
    result: StrictStr
    length: StrictInt
    received_at: StrictStr

    @classmethod
    def from_text(cls, text: str) -> EchoResponse:
        return cls(
            result=text,
            length=len(text),
            received_at=datetime.now(timezone.utc).isoformat()
        )
