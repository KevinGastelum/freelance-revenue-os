"""Pydantic-style schemas for CLI input/output."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class LeadCreate(BaseModel):
    source: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    budget_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    notes: Optional[str] = None


class LeadSummary(BaseModel):
    id: int
    title: Optional[str]
    source: str
    status: str
    lead_score: Optional[float]
    decision: Optional[str]
