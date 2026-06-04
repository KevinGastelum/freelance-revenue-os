"""SQLModel table models for freelance-os."""

import json
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class JobCategory(str, Enum):
    WEB_APP = "WEB_APP"
    DATA_DASHBOARD = "DATA_DASHBOARD"
    AI_AUTOMATION = "AI_AUTOMATION"
    SCRAPING_DATA = "SCRAPING_DATA"
    WORDPRESS = "WORDPRESS"
    BUG_FIX = "BUG_FIX"
    OTHER = "OTHER"


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


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(default="manual")
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    client_rating: Optional[float] = None
    client_payment_verified: bool = Field(default=False)
    budget_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None
    country: Optional[str] = None
    posted_at: Optional[datetime] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    status: LeadStatus = Field(default=LeadStatus.NEW)
    lead_score: Optional[int] = None
    risk_score: Optional[int] = None
    decision: Optional[Decision] = None
    reason_codes: Optional[str] = None  # JSON-encoded list[str]
    raw_payload: Optional[str] = None   # JSON-encoded dict
    notes: Optional[str] = None
    category: str = Field(default=JobCategory.OTHER.value)


class ProposalDraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    version: int = Field(default=1)
    draft_text: Optional[str] = None
    technical_diagnosis: Optional[str] = None
    portfolio_matches: Optional[str] = None   # JSON list[str]
    clarifying_questions: Optional[str] = None  # JSON list[str]
    price_recommendation: Optional[str] = None
    validator_flags: Optional[str] = None      # JSON dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by_user: bool = Field(default=False)


class PortfolioItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None     # JSON list[str]
    proof_points: Optional[str] = None   # JSON list[str]
    links: Optional[str] = None          # JSON list[str]
    allowed_claims: Optional[str] = None  # JSON list[str]
    forbidden_claims: Optional[str] = None  # JSON list[str]
    tags: Optional[str] = None           # JSON list[str]


class ClientProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    client_name: str
    project_name: str
    platform: Optional[str] = None
    contract_url: Optional[str] = None
    status: ClientProjectStatus = Field(default=ClientProjectStatus.INTAKE)
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    scope_path: Optional[str] = None
    workspace_path: Optional[str] = None
    repo_url: Optional[str] = None
    branch_name: Optional[str] = None
    delivery_path: Optional[str] = None


class Outcome(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    result: OutcomeResult
    reason: Optional[str] = None
    final_rate: Optional[float] = None
    final_budget: Optional[float] = None
    time_spent_hours: Optional[float] = None
    profit_estimate: Optional[float] = None
    lessons: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


def encode_json(value: object) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def decode_json(value: Optional[str]) -> object:
    if value is None:
        return None
    return json.loads(value)
