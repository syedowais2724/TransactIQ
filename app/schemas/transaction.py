"""
Pydantic schemas for Transaction-related API responses.
"""
from datetime import date
from typing import Optional, Any
from pydantic import BaseModel, field_validator

from app.utils.data_cleaner import FALLBACK_CATEGORY, MISSING_CATEGORY, normalize_category_value


class TransactionResponse(BaseModel):
    id: int
    job_id: int
    txn_id: str
    date: date
    merchant: str
    amount: float
    currency: str
    status: str
    category: Optional[str] = None
    account_id: str
    notes: Optional[str] = None
    is_anomaly: bool
    anomaly_reason: Optional[str] = None
    llm_category: Optional[str] = None
    llm_failed: bool

    @field_validator("txn_id", mode="before")
    @classmethod
    def sanitize_txn_id(cls, value: Any) -> str:
        text = "" if value is None else str(value).strip()
        if text.lower() in {"", "nan", "none", "null", "undefined"}:
            return "AUTO_TXN_UNKNOWN"
        return text

    @field_validator("category", mode="before")
    @classmethod
    def sanitize_category(cls, value: Any) -> str:
        category = normalize_category_value(value, FALLBACK_CATEGORY)
        return FALLBACK_CATEGORY if category == MISSING_CATEGORY else category

    class Config:
        from_attributes = True
