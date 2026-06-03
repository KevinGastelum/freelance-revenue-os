"""SQLModel data models for Freelance Revenue OS."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Column, Field, SQLModel, Text


class LeadStatus(str, Enum):
    NEW = "NEW"
    SCORED = "SCORED"
    DRAFTED = "DRAFTED"
    APPROVED_TO_APPLY = "APPROVED_TO_APPLY"
    APPLIED_MANUALLY = "APPLIED_MANUALLY"
    INTERVIEW = "INTERVIEW"
    WON = "WON"
    LOST = "LOST"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class Decision(str, Enum):
    DRAFT_NOW = "DRAFT_NOW"
    WATCH = "WATCH"
    MAYBE = "MAYBE"
    REJECT = "REJECT"


class ClientProjectStatus(str, Enum):
    INTAKE = "INTAKE"
    ACTIVE = "ACTIVE"
    WAITING_ON_CLIENT = "WAITING_ON_CLIENT"
    READY_FOR_DELIVERY = "READY_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    REVISION = "REVISION"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"


class OutcomeResult(str, Enum):
    WON = "WON"
    LOST = "LOST"
    NO_RESPONSE = "NO_RESPONSE"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(default="manual")
    source_url: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    client_name: Optional[str] = Field(default=None)
    client_rating: Optional[float] = Field(default=None)
    client_payment_verified: bool = Field(default=False)
    budget_type: Optional[str] = Field(default=None)
    budget_min: Optional[float] = Field(default=None)
    budget_max: Optional[float] = Field(default=None)
    hourly_min: Optional[float] = Field(default=None)
    hourly_max: Optional[float] = Field(default=None)
    country: Optional[str] = Field(default=None)
    posted_at: Optional[datetime] = Field(default=None)
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    status: LeadStatus = Field(default=LeadStatus.NEW)
    lead_score: Optional[float] = Field(default=None)
    risk_score: Optional[float] = Field(default=None)
    decision: Optional[Decision] = Field(default=None)
    reason_codes: Optional[str] = Field(default=None, sa_column=Column(Text))
    raw_payload: Optional[str] = Field(default=None, sa_column=Column(Text))
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))

    def get_reason_codes(self) -> list[str]:
        if not self.reason_codes:
            return []
        try:
            return json.loads(self.reason_codes)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_reason_codes(self, codes: list[str]) -> None:
        self.reason_codes = json.dumps(codes)


class ProposalDraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    version: int = Field(default=1)
    draft_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    technical_diagnosis: Optional[str] = Field(default=None, sa_column=Column(Text))
    portfolio_matches: Optional[str] = Field(default=None, sa_column=Column(Text))
    clarifying_questions: Optional[str] = Field(default=None, sa_column=Column(Text))
    price_recommendation: Optional[str] = Field(default=None, sa_column=Column(Text))
    validator_flags: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by_user: bool = Field(default=False)


class PortfolioItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    tech_stack: Optional[str] = Field(default=None, sa_column=Column(Text))
    proof_points: Optional[str] = Field(default=None, sa_column=Column(Text))
    links: Optional[str] = Field(default=None, sa_column=Column(Text))
    allowed_claims: Optional[str] = Field(default=None, sa_column=Column(Text))
    forbidden_claims: Optional[str] = Field(default=None, sa_column=Column(Text))
    tags: Optional[str] = Field(default=None, sa_column=Column(Text))


class ClientProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: Optional[int] = Field(default=None, foreign_key="lead.id")
    client_name: str
    project_name: str
    platform: Optional[str] = Field(default=None)
    contract_url: Optional[str] = Field(default=None)
    status: ClientProjectStatus = Field(default=ClientProjectStatus.INTAKE)
    start_date: Optional[datetime] = Field(default=None)
    deadline: Optional[datetime] = Field(default=None)
    scope_path: Optional[str] = Field(default=None)
    workspace_path: Optional[str] = Field(default=None)
    repo_url: Optional[str] = Field(default=None)
    branch_name: Optional[str] = Field(default=None)
    delivery_path: Optional[str] = Field(default=None)


class Outcome(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    result: OutcomeResult
    reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    final_rate: Optional[float] = Field(default=None)
    final_budget: Optional[float] = Field(default=None)
    time_spent_hours: Optional[float] = Field(default=None)
    profit_estimate: Optional[float] = Field(default=None)
    lessons: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
