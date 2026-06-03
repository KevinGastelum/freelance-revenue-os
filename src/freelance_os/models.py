from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from .schemas import ClientProjectStatus, Decision, LeadStatus, OutcomeResult


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    client_rating: Optional[float] = None
    client_payment_verified: Optional[bool] = None
    budget_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None
    country: Optional[str] = None
    posted_at: Optional[datetime] = None
    imported_at: datetime = Field(default_factory=datetime.utcnow)
    status: LeadStatus = Field(default=LeadStatus.NEW)
    lead_score: Optional[float] = None
    risk_score: Optional[float] = None
    decision: Optional[Decision] = None
    reason_codes: Optional[str] = None
    raw_payload: Optional[str] = None
    notes: Optional[str] = None


class ProposalDraft(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: int = Field(foreign_key="lead.id")
    version: int = Field(default=1)
    draft_text: Optional[str] = None
    technical_diagnosis: Optional[str] = None
    portfolio_matches: Optional[str] = None
    clarifying_questions: Optional[str] = None
    price_recommendation: Optional[str] = None
    validator_flags: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by_user: bool = Field(default=False)


class PortfolioItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: Optional[str] = None
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    proof_points: Optional[str] = None
    links: Optional[str] = None
    allowed_claims: Optional[str] = None
    forbidden_claims: Optional[str] = None
    tags: Optional[str] = None


class ClientProject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lead_id: Optional[int] = Field(default=None, foreign_key="lead.id")
    client_name: Optional[str] = None
    project_name: Optional[str] = None
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
    lead_id: Optional[int] = Field(default=None, foreign_key="lead.id")
    result: Optional[OutcomeResult] = None
    reason: Optional[str] = None
    final_rate: Optional[float] = None
    final_budget: Optional[float] = None
    time_spent_hours: Optional[float] = None
    profit_estimate: Optional[float] = None
    lessons: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
