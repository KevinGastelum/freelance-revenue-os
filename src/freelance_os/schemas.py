"""Pydantic schemas for API/CLI input validation (separate from ORM models)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class LeadCreate(BaseModel):
    source: str = "manual"
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    budget_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    notes: Optional[str] = None


class OutcomeCreate(BaseModel):
    lead_id: int
    result: str
    reason: Optional[str] = None
    final_rate: Optional[float] = None
    final_budget: Optional[float] = None
    time_spent_hours: Optional[float] = None
    profit_estimate: Optional[float] = None
    lessons: Optional[str] = None
