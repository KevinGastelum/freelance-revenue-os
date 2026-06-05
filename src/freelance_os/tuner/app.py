"""Metric-tuning web console + Command Center dashboard FastAPI app.

Bound strictly to 127.0.0.1 — no external network calls.
Preview endpoint is read-only: never mutates the database.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Module-level config (set via configure() before starting)
# ---------------------------------------------------------------------------
_db_path: str = "data/freelance_os.sqlite"
_scoring_rules_path: str = "config/scoring_rules.toml"
_config_dir: str = "config"


def configure(
    db_path: str,
    scoring_rules_path: str = "config/scoring_rules.toml",
    config_dir: str = "config",
) -> None:
    """Set runtime paths — call before uvicorn.run() or in tests."""
    global _db_path, _scoring_rules_path, _config_dir
    _db_path = db_path
    _scoring_rules_path = scoring_rules_path
    _config_dir = config_dir


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class WeightsModel(BaseModel):
    technical_fit: float = 20
    budget_fit: float = 15
    client_quality: float = 15
    clarity_of_scope: float = 10
    urgency_timing: float = 10
    portfolio_match: float = 10
    repeat_work_potential: float = 10
    communication_quality: float = 10


class ThresholdsModel(BaseModel):
    draft_now_min: float = 80
    watch_min: float = 65
    maybe_min: float = 50


class RiskPenaltiesModel(BaseModel):
    unpaid_test_request: float = 25
    payment_rule_bypass: float = 25
    unrealistic_deadline: float = 20
    vague_fixed_low_budget: float = 20
    suspicious_payment: float = 15
    scope_creep_risk: float = 15
    easy_language_complex_work: float = 10
    unclear_deliverables: float = 10
    unsupported_tech_stack: float = 10
    free_consultation_request: float = 10


class PricingModel(BaseModel):
    target_hourly_rate: float = 75
    minimum_project_value: float = 300
    risk_multiplier_low: float = 1.0
    risk_multiplier_medium: float = 1.25
    risk_multiplier_high: float = 1.5
    rush_multiplier: float = 1.25
    platform_fee_buffer: float = 0.10


class ScoringRulesModel(BaseModel):
    weights: WeightsModel = WeightsModel()
    thresholds: ThresholdsModel = ThresholdsModel()
    risk_penalties: RiskPenaltiesModel = RiskPenaltiesModel()
    pricing: PricingModel = PricingModel()


class ActionRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# TOML helpers
# ---------------------------------------------------------------------------

def _load_scoring_rules_from_path(path: str) -> ScoringRulesModel:
    """Load scoring rules from TOML, falling back to example then defaults."""
    import sys
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore[no-redef]

    candidates = [path, "config/scoring_rules.toml", "config/scoring_rules.example.toml"]
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            with open(p, "rb") as f:
                data = tomllib.load(f)
            return ScoringRulesModel(
                weights=WeightsModel(**{k: float(v) for k, v in data.get("weights", {}).items()}),
                thresholds=ThresholdsModel(**{k: float(v) for k, v in data.get("thresholds", {}).items()}),
                risk_penalties=RiskPenaltiesModel(**{k: float(v) for k, v in data.get("risk_penalties", {}).items()}),
                pricing=PricingModel(**{k: float(v) for k, v in data.get("pricing", {}).items()}),
            )
    return ScoringRulesModel()


def _write_toml(params: ScoringRulesModel, path: str) -> None:
    """Write scoring rules to a TOML file (cross-platform, utf-8)."""

    def fmt_int(v: float) -> str:
        return str(int(round(v)))

    def fmt_float(v: float) -> str:
        if v == int(v):
            return f"{int(v)}.0"
        return str(round(v, 6))

    w = params.weights
    t = params.thresholds
    rp = params.risk_penalties
    p = params.pricing

    content = (
        "# scoring_rules.toml — saved by freelance-os tune\n"
        "# Edit via `freelance-os tune` or manually.\n"
        "\n[thresholds]\n"
        f"draft_now_min = {fmt_int(t.draft_now_min)}\n"
        f"watch_min = {fmt_int(t.watch_min)}\n"
        f"maybe_min = {fmt_int(t.maybe_min)}\n"
        "\n[weights]\n"
        f"technical_fit = {fmt_int(w.technical_fit)}\n"
        f"budget_fit = {fmt_int(w.budget_fit)}\n"
        f"client_quality = {fmt_int(w.client_quality)}\n"
        f"clarity_of_scope = {fmt_int(w.clarity_of_scope)}\n"
        f"urgency_timing = {fmt_int(w.urgency_timing)}\n"
        f"portfolio_match = {fmt_int(w.portfolio_match)}\n"
        f"repeat_work_potential = {fmt_int(w.repeat_work_potential)}\n"
        f"communication_quality = {fmt_int(w.communication_quality)}\n"
        "\n[risk_penalties]\n"
        f"unpaid_test_request = {fmt_int(rp.unpaid_test_request)}\n"
        f"payment_rule_bypass = {fmt_int(rp.payment_rule_bypass)}\n"
        f"unrealistic_deadline = {fmt_int(rp.unrealistic_deadline)}\n"
        f"vague_fixed_low_budget = {fmt_int(rp.vague_fixed_low_budget)}\n"
        f"suspicious_payment = {fmt_int(rp.suspicious_payment)}\n"
        f"scope_creep_risk = {fmt_int(rp.scope_creep_risk)}\n"
        f"easy_language_complex_work = {fmt_int(rp.easy_language_complex_work)}\n"
        f"unclear_deliverables = {fmt_int(rp.unclear_deliverables)}\n"
        f"unsupported_tech_stack = {fmt_int(rp.unsupported_tech_stack)}\n"
        f"free_consultation_request = {fmt_int(rp.free_consultation_request)}\n"
        "\n[pricing]\n"
        f"target_hourly_rate = {fmt_int(p.target_hourly_rate)}\n"
        f"minimum_project_value = {fmt_int(p.minimum_project_value)}\n"
        f"risk_multiplier_low = {fmt_float(p.risk_multiplier_low)}\n"
        f"risk_multiplier_medium = {fmt_float(p.risk_multiplier_medium)}\n"
        f"risk_multiplier_high = {fmt_float(p.risk_multiplier_high)}\n"
        f"rush_multiplier = {fmt_float(p.rush_multiplier)}\n"
        f"platform_fee_buffer = {fmt_float(p.platform_fee_buffer)}\n"
    )

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Scoring helpers (in-memory, no DB writes)
# ---------------------------------------------------------------------------

def _params_to_scoring_cfg(params: ScoringRulesModel) -> dict:
    """Convert ScoringRulesModel to the dict format score_lead() expects."""
    return {
        "scoring_rules": {
            "weights": params.weights.model_dump(),
            "thresholds": params.thresholds.model_dump(),
            "risk_penalties": params.risk_penalties.model_dump(),
        },
        "scoring": {
            "target_hourly_rate": params.pricing.target_hourly_rate,
            "minimum_project_value": params.pricing.minimum_project_value,
            "risk_multiplier_low": params.pricing.risk_multiplier_low,
            "risk_multiplier_medium": params.pricing.risk_multiplier_medium,
            "risk_multiplier_high": params.pricing.risk_multiplier_high,
            "rush_multiplier": params.pricing.rush_multiplier,
        },
    }


def _compute_preview(params: ScoringRulesModel) -> dict:
    """Re-score all leads in-memory. Returns markers + per-lead results."""
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, Outcome, OutcomeResult
    from freelance_os.scoring.lead_scorer import score_lead
    from sqlmodel import Session, select

    engine = get_engine(_db_path)
    cfg = _params_to_scoring_cfg(params)

    with Session(engine) as session:
        leads = session.exec(select(Lead)).all()
        outcomes = session.exec(select(Outcome)).all()

    outcome_map: Dict[int, str] = {o.lead_id: o.result.value for o in outcomes}

    lead_results = []
    all_new_scores: List[int] = []
    all_old_scores: List[int] = []
    dist_before: Dict[str, int] = defaultdict(int)
    dist_after: Dict[str, int] = defaultdict(int)
    code_counter: Counter = Counter()
    wins_by_old_dec: Dict[str, List[bool]] = defaultdict(list)
    wins_by_new_dec: Dict[str, List[bool]] = defaultdict(list)

    for lead in leads:
        new_result = score_lead(lead, cfg)
        new_score = new_result["lead_score"]
        new_decision = new_result["decision"]
        new_codes = new_result["reason_codes"]

        old_score = lead.lead_score
        old_decision = lead.decision.value if lead.decision else None

        if old_score is not None:
            all_old_scores.append(old_score)
        if old_decision:
            dist_before[old_decision] += 1
        dist_after[new_decision] += 1
        all_new_scores.append(new_score)
        code_counter.update(new_codes)

        delta = new_score - (old_score if old_score is not None else new_score)
        decision_changed = (old_decision is not None) and (old_decision != new_decision)

        outcome = outcome_map.get(lead.id) if lead.id is not None else None
        if outcome is not None:
            won = (outcome == OutcomeResult.WON.value)
            if old_decision:
                wins_by_old_dec[old_decision].append(won)
            wins_by_new_dec[new_decision].append(won)

        lead_results.append({
            "id": lead.id,
            "title": lead.title or "",
            "source": lead.source,
            "old_score": old_score,
            "new_score": new_score,
            "old_decision": old_decision,
            "new_decision": new_decision,
            "delta": delta,
            "decision_changed": decision_changed,
            "outcome": outcome,
            "reason_codes": new_codes,
        })

    decisions = ["DRAFT_NOW", "WATCH", "MAYBE", "REJECT"]

    def win_rate(wins_list: List[bool]) -> Optional[float]:
        if not wins_list:
            return None
        return sum(wins_list) / len(wins_list)

    win_rate_before = {d: win_rate(wins_by_old_dec.get(d, [])) for d in decisions}
    win_rate_after = {d: win_rate(wins_by_new_dec.get(d, [])) for d in decisions}
    outcome_count_before = {d: len(wins_by_old_dec.get(d, [])) for d in decisions}

    changed_count = sum(1 for r in lead_results if r["decision_changed"])

    def _avg(lst: List[int]) -> float:
        return statistics.mean(lst) if lst else 0.0

    def _median(lst: List[int]) -> float:
        return float(statistics.median(lst)) if lst else 0.0

    markers = {
        "changed_decision_count": changed_count,
        "avg_score_before": _avg(all_old_scores),
        "avg_score_after": _avg(all_new_scores),
        "median_score_before": _median(all_old_scores),
        "median_score_after": _median(all_new_scores),
        "distribution_before": dict(dist_before),
        "distribution_after": dict(dist_after),
        "win_rate_by_decision_before": win_rate_before,
        "win_rate_by_decision_after": win_rate_after,
        "outcome_count_by_decision_before": outcome_count_before,
        "top_reason_codes": code_counter.most_common(15),
    }

    return {"leads": lead_results, "markers": markers}


# ---------------------------------------------------------------------------
# Dashboard helpers
# ---------------------------------------------------------------------------

def _lead_to_dict(lead: Any) -> dict:
    """Serialize a Lead model instance to a JSON-safe dict."""
    import json as _json

    def _val(x: Any) -> Optional[str]:
        if x is None:
            return None
        return x.value if hasattr(x, "value") else str(x)

    return {
        "id": lead.id,
        "source": lead.source,
        "source_url": lead.source_url,
        "title": lead.title or "",
        "description": lead.description or "",
        "category": lead.category or "OTHER",
        "status": _val(lead.status),
        "lead_score": lead.lead_score,
        "risk_score": lead.risk_score,
        "decision": _val(lead.decision),
        "reason_codes": _json.loads(lead.reason_codes) if lead.reason_codes else [],
        "effort_hours_low": lead.effort_hours_low,
        "effort_hours_high": lead.effort_hours_high,
        "feasibility_confidence": lead.feasibility_confidence,
        "warren_feasible": lead.warren_feasible,
        "suggested_price": lead.suggested_price,
        "suggested_turnaround_days": lead.suggested_turnaround_days,
        "budget_type": lead.budget_type,
        "budget_min": lead.budget_min,
        "budget_max": lead.budget_max,
        "hourly_min": lead.hourly_min,
        "hourly_max": lead.hourly_max,
        "client_name": lead.client_name,
        "client_rating": lead.client_rating,
        "client_payment_verified": lead.client_payment_verified,
        "imported_at": lead.imported_at.isoformat() if lead.imported_at else None,
        "posted_at": lead.posted_at.isoformat() if lead.posted_at else None,
    }


def _build_action_cfg() -> dict:
    """Build a cfg dict suitable for scoring / feasibility / proposal actions."""
    sr = _load_scoring_rules_from_path(_scoring_rules_path)
    return {
        "scoring_rules": {
            "weights": sr.weights.model_dump(),
            "thresholds": sr.thresholds.model_dump(),
            "risk_penalties": sr.risk_penalties.model_dump(),
        },
        "scoring": {
            "target_hourly_rate": sr.pricing.target_hourly_rate,
            "minimum_project_value": sr.pricing.minimum_project_value,
            "risk_multiplier_low": sr.pricing.risk_multiplier_low,
            "risk_multiplier_medium": sr.pricing.risk_multiplier_medium,
            "risk_multiplier_high": sr.pricing.risk_multiplier_high,
            "rush_multiplier": sr.pricing.rush_multiplier,
            "quick_win_discount": 0.85,
        },
        "paths": {
            "database_path": _db_path,
            "portfolio_file": str(Path(_config_dir) / "portfolio.yaml"),
        },
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Freelance OS Command Center", version="0.2.0")

_STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
def serve_ui() -> HTMLResponse:
    html_path = _STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=500)


# ---------------------------------------------------------------------------
# Tuner (settings) endpoints — read-only preview, save to TOML
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config() -> dict:
    """Return current scoring rules as JSON."""
    sr = _load_scoring_rules_from_path(_scoring_rules_path)
    return sr.model_dump()


@app.post("/api/preview")
def preview(params: ScoringRulesModel) -> dict:
    """Re-score all leads in-memory with candidate params. Never mutates DB."""
    return _compute_preview(params)


@app.post("/api/save")
def save_config(params: ScoringRulesModel) -> dict:
    """Write params to scoring_rules.toml."""
    path = _scoring_rules_path or "config/scoring_rules.toml"
    _write_toml(params, path)
    return {"status": "saved", "path": path}


@app.get("/api/presets")
def list_presets() -> List[str]:
    """List available preset names."""
    presets_dir = Path("config/presets")
    if not presets_dir.exists():
        return []
    return sorted(
        p.stem for p in presets_dir.iterdir() if p.suffix == ".toml"
    )


@app.get("/api/presets/{name}")
def get_preset(name: str) -> dict:
    """Load a named preset."""
    path = Path("config/presets") / f"{name}.toml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Preset '{name}' not found")
    sr = _load_scoring_rules_from_path(str(path))
    return sr.model_dump()


@app.post("/api/presets/{name}")
def save_preset(name: str, params: ScoringRulesModel) -> dict:
    """Save current params as a named preset."""
    presets_dir = Path("config/presets")
    presets_dir.mkdir(parents=True, exist_ok=True)
    path = presets_dir / f"{name}.toml"
    _write_toml(params, str(path))
    return {"status": "saved", "preset": name, "path": str(path)}


# ---------------------------------------------------------------------------
# Dashboard — lead board endpoints
# ---------------------------------------------------------------------------

@app.get("/api/leads")
def list_leads(
    category: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    min_score: Optional[int] = None,
    warren_feasible: Optional[bool] = None,
    quickwins_only: bool = False,
    sort_by: str = "id",
    order: str = "desc",
) -> List[dict]:
    """Return leads with optional filters and sort."""
    from freelance_os.db import get_engine
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    engine = get_engine(_db_path)
    with Session(engine) as session:
        stmt = select(Lead)
        if category:
            stmt = stmt.where(Lead.category == category.upper())
        if source:
            stmt = stmt.where(Lead.source == source)
        if status:
            stmt = stmt.where(Lead.status == status.upper())
        if decision:
            stmt = stmt.where(Lead.decision == decision.upper())
        if warren_feasible is not None:
            stmt = stmt.where(Lead.warren_feasible == warren_feasible)  # noqa: E712
        leads = session.exec(stmt).all()

    if min_score is not None:
        leads = [l for l in leads if l.lead_score is not None and l.lead_score >= min_score]

    if quickwins_only:
        leads = [
            l for l in leads
            if l.warren_feasible
            and l.feasibility_confidence in ("MED", "HIGH")
            and l.effort_hours_high is not None
        ]

    reverse = order.lower() == "desc"
    if sort_by == "score":
        leads = sorted(leads, key=lambda l: (l.lead_score or 0), reverse=reverse)
    elif sort_by == "effort":
        leads = sorted(leads, key=lambda l: (l.effort_hours_high or 9999), reverse=reverse)
    elif sort_by == "price":
        leads = sorted(leads, key=lambda l: (l.suggested_price or 0), reverse=reverse)
    else:
        leads = sorted(leads, key=lambda l: (l.id or 0), reverse=reverse)

    return [_lead_to_dict(l) for l in leads]


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: int) -> dict:
    """Return full lead detail including latest proposal draft."""
    import json as _json
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, ProposalDraft
    from sqlmodel import Session, select

    engine = get_engine(_db_path)
    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        draft = session.exec(
            select(ProposalDraft)
            .where(ProposalDraft.lead_id == lead_id)
            .order_by(ProposalDraft.version.desc())  # type: ignore[arg-type]
        ).first()

        result = _lead_to_dict(lead)

        if draft:
            result["draft"] = {
                "id": draft.id,
                "version": draft.version,
                "draft_text": draft.draft_text or "",
                "technical_diagnosis": draft.technical_diagnosis or "",
                "portfolio_matches": _json.loads(draft.portfolio_matches) if draft.portfolio_matches else [],
                "clarifying_questions": _json.loads(draft.clarifying_questions) if draft.clarifying_questions else [],
                "price_recommendation": draft.price_recommendation or "",
                "validator_flags": _json.loads(draft.validator_flags) if draft.validator_flags else None,
                "approved_by_user": draft.approved_by_user,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
            }
        else:
            result["draft"] = None

    return result


@app.post("/api/leads/{lead_id}/action")
def lead_action(lead_id: int, body: ActionRequest) -> dict:
    """Perform an action on a lead and persist the result to the DB."""
    import json as _json
    from freelance_os.db import get_engine
    from freelance_os.models import Lead, LeadStatus, ProposalDraft
    from sqlmodel import Session, select

    engine = get_engine(_db_path)
    cfg = _build_action_cfg()

    with Session(engine) as session:
        lead = session.get(Lead, lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

        action = body.action

        if action == "score":
            from freelance_os.scoring.lead_scorer import score_lead
            result = score_lead(lead, cfg)
            lead.lead_score = result["lead_score"]
            lead.risk_score = result["risk_score"]
            lead.decision = result["decision"]
            lead.reason_codes = _json.dumps(result["reason_codes"])
            lead.status = LeadStatus.SCORED
            session.add(lead)
            session.commit()
            return {"action": "score", "result": result}

        elif action == "estimate":
            from freelance_os.scoring.feasibility import estimate_feasibility
            result = estimate_feasibility(lead, cfg)
            lead.effort_hours_low = result["effort_hours_low"]
            lead.effort_hours_high = result["effort_hours_high"]
            lead.feasibility_confidence = result["feasibility_confidence"]
            lead.warren_feasible = result["warren_feasible"]
            lead.suggested_price = result["suggested_price"]
            lead.suggested_turnaround_days = result["suggested_turnaround_days"]
            session.add(lead)
            session.commit()
            return {"action": "estimate", "result": result}

        elif action == "draft":
            from freelance_os.proposal.draft_generator import generate_draft
            draft_data = generate_draft(lead, cfg)
            draft = ProposalDraft(
                lead_id=lead_id,
                draft_text=draft_data["draft_text"],
                technical_diagnosis=draft_data["technical_diagnosis"],
                portfolio_matches=_json.dumps(draft_data.get("portfolio_matches", [])),
                clarifying_questions=_json.dumps(draft_data.get("clarifying_questions", [])),
                price_recommendation=draft_data.get("price_recommendation"),
            )
            session.add(draft)
            lead.status = LeadStatus.DRAFTED
            session.add(lead)
            session.commit()
            session.refresh(draft)
            return {
                "action": "draft",
                "draft_id": draft.id,
                "draft_text": draft_data["draft_text"],
            }

        elif action == "validate":
            draft = session.exec(
                select(ProposalDraft)
                .where(ProposalDraft.lead_id == lead_id)
                .order_by(ProposalDraft.version.desc())  # type: ignore[arg-type]
            ).first()
            if draft is None:
                raise HTTPException(
                    status_code=400,
                    detail="No draft found. Run 'draft' action first.",
                )
            from freelance_os.proposal.proposal_validator import validate_draft
            result = validate_draft(draft, cfg)
            draft.validator_flags = _json.dumps(result)
            session.add(draft)
            session.commit()
            return {"action": "validate", "result": result}

        elif action == "status":
            new_status_str = body.params.get("status", "").upper()
            try:
                new_status = LeadStatus(new_status_str)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status '{new_status_str}'. Valid: {[s.value for s in LeadStatus]}",
                )
            lead.status = new_status
            session.add(lead)
            session.commit()
            return {"action": "status", "new_status": new_status.value}

        elif action == "save_draft":
            draft = session.exec(
                select(ProposalDraft)
                .where(ProposalDraft.lead_id == lead_id)
                .order_by(ProposalDraft.version.desc())  # type: ignore[arg-type]
            ).first()
            if draft is None:
                raise HTTPException(
                    status_code=400,
                    detail="No draft found. Run 'draft' action first.",
                )
            draft.draft_text = body.params.get("draft_text", "")
            session.add(draft)
            session.commit()
            return {"action": "save_draft", "saved": True}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action!r}")


# ---------------------------------------------------------------------------
# Dashboard — sources + quickwins endpoints
# ---------------------------------------------------------------------------

@app.get("/api/sources")
def get_sources(
    category: Optional[str] = None,
    newcomer: Optional[bool] = None,
    region: Optional[str] = None,
) -> List[dict]:
    """Return filtered freelance platform source directory."""
    from freelance_os.sources import filter_sources, load_sources

    sources = load_sources(_config_dir)
    return filter_sources(
        sources,
        category=category,
        newcomer=bool(newcomer) if newcomer is not None else False,
        region=region,
    )


@app.get("/api/reputation")
def get_reputation() -> dict:
    """Return reputation metrics: overall, per-platform, momentum."""
    from freelance_os.reports.reputation import aggregate_reputation

    cfg = {"paths": {"database_path": _db_path}}
    return aggregate_reputation(cfg)


@app.get("/api/quickwins")
def get_quickwins(limit: int = 20) -> List[dict]:
    """Return top quick-win leads: warren-feasible, MED/HIGH confidence, sorted by score/effort."""
    from freelance_os.db import get_engine
    from freelance_os.models import Lead
    from sqlmodel import Session, select

    engine = get_engine(_db_path)
    with Session(engine) as session:
        leads = session.exec(
            select(Lead).where(Lead.warren_feasible == True)  # noqa: E712
        ).all()

    leads = [
        l for l in leads
        if l.feasibility_confidence in ("MED", "HIGH")
        and l.effort_hours_high is not None
    ]

    def _priority(lead: Any) -> float:
        score = lead.lead_score if lead.lead_score is not None else 50
        return score / lead.effort_hours_high

    leads = sorted(leads, key=_priority, reverse=True)
    return [_lead_to_dict(l) for l in leads[:limit]]
