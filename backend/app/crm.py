from datetime import datetime, timedelta, timezone
from typing import Optional
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    JSON, func, or_, and_
)
from sqlalchemy.orm import Session

from app.core.database import Base, get_db

router = APIRouter(tags=["NexLead CRM"])


# ============================================================
# DATABASE MODELS
# ============================================================

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(180), nullable=False, unique=True)
    industry = Column(String(100))
    website = Column(String(255))
    territory = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String(150), nullable=False)
    email = Column(String(180), index=True)
    phone = Column(String(40))
    job_title = Column(String(120))
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    channel = Column(String(60))
    status = Column(String(30), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesRep(Base):
    __tablename__ = "sales_reps"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(180), unique=True)
    territory = Column(String(100), nullable=False, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(30), unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    assigned_rep_id = Column(Integer, ForeignKey("sales_reps.id"))
    name = Column(String(150), nullable=False)
    email = Column(String(180), index=True)
    source = Column(String(80), default="Website")
    territory = Column(String(100))
    status = Column(String(40), default="New")
    fit_score = Column(Float, default=0)
    intent_score = Column(Float, default=0)
    engagement_score = Column(Float, default=0)
    total_score = Column(Float, default=0)
    score_explanation = Column(JSON)
    consent_status = Column(String(30), default="unknown")
    last_activity_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadCampaign(Base):
    __tablename__ = "lead_campaigns"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    linked_at = Column(DateTime, default=datetime.utcnow)


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    activity_type = Column(String(60), nullable=False)
    description = Column(Text)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON)


class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    purpose = Column(String(60), default="marketing")
    status = Column(String(30), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(80))


class ScoreRule(Base):
    __tablename__ = "score_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    fit_weight = Column(Float, default=40)
    intent_weight = Column(Float, default=35)
    engagement_weight = Column(Float, default=25)
    active = Column(Boolean, default=True)
    effective_from = Column(DateTime, default=datetime.utcnow)


class ScoreSnapshot(Base):
    """Immutable record of a lead score at a specific point in time."""
    __tablename__ = "score_snapshots"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    scored_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    fit_score = Column(Float, nullable=False)
    intent_score = Column(Float, nullable=False)
    engagement_score = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    explanation = Column(JSON)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    public_id = Column(String(35), unique=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    assigned_rep_id = Column(Integer, ForeignKey("sales_reps.id"))
    title = Column(String(180), nullable=False)
    description = Column(Text)
    due_at = Column(DateTime)
    priority = Column(String(20), default="Medium")
    status = Column(String(30), default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True)
    public_id = Column(String(35), unique=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    name = Column(String(180), nullable=False)
    amount = Column(Float, default=0)
    stage = Column(String(40), default="Qualified")
    probability = Column(Float, default=20)
    expected_close_date = Column(DateTime)
    outcome_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StageHistory(Base):
    __tablename__ = "stage_history"
    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    from_stage = Column(String(40))
    to_stage = Column(String(40), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(Text)


# ============================================================
# SCORING AND SERIALIZATION
# ============================================================

def calculate_score(fit, intent, engagement, db):
    values = [float(fit), float(intent), float(engagement)]
    if any(value < 0 or value > 100 for value in values):
        raise HTTPException(422, "Score components must be between 0 and 100")

    rule = db.query(ScoreRule).filter(ScoreRule.active.is_(True)).order_by(
        ScoreRule.effective_from.desc(), ScoreRule.id.desc()
    ).first()
    fw, iw, ew = (
        (float(rule.fit_weight), float(rule.intent_weight), float(rule.engagement_weight))
        if rule else (40.0, 35.0, 25.0)
    )
    weights = [fw, iw, ew]
    if any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise HTTPException(500, "Active scoring rule has invalid weights")

    total_weight = sum(weights)
    components = {
        "fit": round(values[0] * fw / total_weight, 2),
        "intent": round(values[1] * iw / total_weight, 2),
        "engagement": round(values[2] * ew / total_weight, 2),
    }
    total = round(sum(components.values()), 2)
    return total, {
        "components": components,
        "weights": {"fit": fw, "intent": iw, "engagement": ew},
        "method": "Weighted rule-based score",
        "interpretation": "Hot" if total >= 75 else "Warm" if total >= 45 else "Cold",
    }


def latest_consent(db, lead_id, purpose="marketing"):
    return db.query(Consent).filter(
        Consent.lead_id == lead_id,
        func.lower(Consent.purpose) == purpose.lower()
    ).order_by(Consent.recorded_at.desc(), Consent.id.desc()).first()


def is_marketing_action(value):
    text = str(value or "").lower().replace("_", " ").replace("-", " ")
    keywords = ("marketing", "campaign", "promotional", "newsletter", "bulk email")
    return any(keyword in text for keyword in keywords)


def validate_marketing_consent(db, lead, action):
    if not is_marketing_action(action):
        return
    consent = latest_consent(db, lead.id, "marketing")
    status = consent.status.lower() if consent else (lead.consent_status or "unknown").lower()
    if status != "granted":
        raise HTTPException(403, {
            "code": "MARKETING_CONSENT_REQUIRED",
            "message": "Marketing communication blocked because current marketing consent is not granted",
            "lead_id": lead.id,
            "consent_status": status,
        })


def matching_rep(db, territory):
    if not territory:
        return None
    return db.query(SalesRep).filter(
        SalesRep.active.is_(True),
        func.lower(SalesRep.territory) == territory.strip().lower()
    ).order_by(SalesRep.id).first()


def save_score_snapshot(db, lead, explanation, scored_at=None):
    db.add(ScoreSnapshot(
        lead_id=lead.id,
        scored_at=scored_at or datetime.utcnow(),
        fit_score=lead.fit_score,
        intent_score=lead.intent_score,
        engagement_score=lead.engagement_score,
        total_score=lead.total_score,
        explanation=explanation,
    ))


def lead_dict(lead, db):
    company = db.get(Company, lead.company_id) if lead.company_id else None
    rep = db.get(SalesRep, lead.assigned_rep_id) if lead.assigned_rep_id else None
    return {
        "id": lead.id,
        "public_id": lead.public_id,
        "name": lead.name,
        "email": lead.email,
        "company": company.name if company else None,
        "company_id": lead.company_id,
        "contact_id": lead.contact_id,
        "source": lead.source,
        "territory": lead.territory,
        "status": lead.status,
        "assigned_rep": rep.name if rep else None,
        "assigned_rep_id": lead.assigned_rep_id,
        "fit_score": lead.fit_score,
        "intent_score": lead.intent_score,
        "engagement_score": lead.engagement_score,
        "total_score": lead.total_score,
        "score_explanation": lead.score_explanation,
        "consent_status": lead.consent_status,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    hot = db.query(Lead).filter(Lead.total_score >= 75).count()
    warm = db.query(Lead).filter(
        Lead.total_score >= 45, Lead.total_score < 75
    ).count()
    cold = db.query(Lead).filter(Lead.total_score < 45).count()

    opportunities = db.query(Opportunity).count()
    won = db.query(Opportunity).filter(Opportunity.stage == "Won").count()
    pipeline = db.query(func.coalesce(func.sum(Opportunity.amount), 0)).filter(
        Opportunity.stage.notin_(["Won", "Lost"])
    ).scalar()

    pending_tasks = db.query(Task).filter(Task.status == "Pending").count()
    overdue_tasks = db.query(Task).filter(
        Task.status == "Pending", Task.due_at < datetime.utcnow()
    ).count()

    average_score = db.query(func.coalesce(func.avg(Lead.total_score), 0)).scalar()
    converted_leads = db.query(func.count(func.distinct(Opportunity.lead_id))).filter(Opportunity.stage == "Won").scalar() or 0
    conversion = round(converted_leads / total * 100, 1) if total else 0
    opportunity_win_rate = round(won / opportunities * 100, 1) if opportunities else 0

    stage_rows = db.query(
        Opportunity.stage, func.count(Opportunity.id)
    ).group_by(Opportunity.stage).all()

    source_rows = db.query(
        Lead.source, func.count(Lead.id)
    ).group_by(Lead.source).all()

    return {
        "summary": {
            "total_leads": total,
            "hot_leads": hot,
            "warm_leads": warm,
            "cold_leads": cold,
            "opportunities": opportunities,
            "won_opportunities": won,
            "conversion_rate": conversion,
            "opportunity_win_rate": opportunity_win_rate,
            "converted_leads": converted_leads,
            "pipeline_value": float(pipeline or 0),
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks,
            "average_lead_score": round(float(average_score or 0), 1),
        },
        "opportunity_stages": [
            {"stage": stage, "count": count} for stage, count in stage_rows
        ],
        "lead_sources": [
            {"source": source, "count": count} for source, count in source_rows
        ],
    }


# ============================================================
# LEADS
# ============================================================

@router.get("/leads")
def list_leads(
    search: Optional[str] = None,
    status: Optional[str] = None,
    territory: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Lead)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Lead.name.ilike(term),
            Lead.email.ilike(term),
            Lead.public_id.ilike(term)
        ))
    if status:
        query = query.filter(Lead.status == status)
    if territory:
        query = query.filter(Lead.territory == territory)

    total = query.count()
    rows = query.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [lead_dict(x, db) for x in rows], "total": total}


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    activities = db.query(Activity).filter(Activity.lead_id == lead_id).order_by(
        Activity.occurred_at.desc()
    ).all()
    tasks = db.query(Task).filter(Task.lead_id == lead_id).all()
    opportunities = db.query(Opportunity).filter(Opportunity.lead_id == lead_id).all()
    result = lead_dict(lead, db)
    result["activities"] = [
        {"id": a.id, "type": a.activity_type, "description": a.description,
         "occurred_at": a.occurred_at.isoformat()} for a in activities
    ]
    result["tasks"] = [
        {"id": t.id, "title": t.title, "status": t.status,
         "due_at": t.due_at.isoformat() if t.due_at else None} for t in tasks
    ]
    result["opportunities"] = [
        {"id": o.id, "public_id": o.public_id, "name": o.name,
         "amount": o.amount, "stage": o.stage} for o in opportunities
    ]
    return result


@router.post("/leads", status_code=201)
def create_lead(payload: dict, db: Session = Depends(get_db)):
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(422, "Lead name is required")

    email = (payload.get("email") or "").strip().lower() or None
    company_name = (payload.get("company_name") or "Independent").strip()
    territory = (payload.get("territory") or "Unassigned").strip()

    if email:
        duplicate = db.query(Lead).filter(Lead.email == email).first()
        if duplicate:
            raise HTTPException(409, {
                "message": "Possible duplicate lead detected",
                "existing_lead_id": duplicate.id,
                "existing_public_id": duplicate.public_id
            })

    consent = str(payload.get("consent_status", "unknown")).lower()
    if consent not in ("granted", "denied", "unknown"):
        raise HTTPException(422, "consent_status must be granted, denied, or unknown")

    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name, territory=territory)
        db.add(company)
        db.flush()

    contact = Contact(
        company_id=company.id, name=name, email=email,
        phone=payload.get("phone"), job_title=payload.get("job_title")
    )
    db.add(contact)
    db.flush()

    fit = float(payload.get("fit_score", 50))
    intent = float(payload.get("intent_score", 50))
    engagement = float(payload.get("engagement_score", 50))
    if any(x < 0 or x > 100 for x in (fit, intent, engagement)):
        raise HTTPException(422, "Score components must be between 0 and 100")

    score, explanation = calculate_score(fit, intent, engagement, db)

    # Never silently assign a lead outside its territory.
    rep = matching_rep(db, territory)

    lead = Lead(
        public_id=f"LEAD-{datetime.utcnow().year}-PENDING",
        company_id=company.id, contact_id=contact.id,
        assigned_rep_id=rep.id if rep else None,
        name=name, email=email, source=payload.get("source", "Website"),
        territory=territory, status="New",
        fit_score=fit, intent_score=intent, engagement_score=engagement,
        total_score=score, score_explanation=explanation,
        consent_status=consent
    )
    db.add(lead)
    db.flush()
    lead.public_id = f"LEAD-{datetime.utcnow().year}-{lead.id:06d}"
    save_score_snapshot(db, lead, explanation)

    db.add(Consent(
        lead_id=lead.id, purpose="marketing", status=consent,
        source=payload.get("source", "Manual")
    ))
    db.add(Activity(
        lead_id=lead.id, activity_type="Lead Created",
        description="Lead created and initial score calculated"
    ))

    db.commit()
    db.refresh(lead)
    return lead_dict(lead, db)


@router.patch("/leads/{lead_id}/score")
def rescore_lead(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    scored_at = datetime.fromisoformat(payload["scored_at"]) if payload.get("scored_at") else datetime.utcnow()
    if scored_at.tzinfo is not None:
        scored_at = scored_at.astimezone(timezone.utc).replace(tzinfo=None)
    is_historical = bool(payload.get("scored_at")) and scored_at < datetime.utcnow() - timedelta(seconds=1)
    # For historical scoring, start from the latest immutable score snapshot at or
    # before the requested timestamp, never from today's potentially newer score.
    historical_base = None
    if payload.get("scored_at"):
        historical_base = db.query(ScoreSnapshot).filter(
            ScoreSnapshot.lead_id == lead.id,
            ScoreSnapshot.scored_at <= scored_at
        ).order_by(ScoreSnapshot.scored_at.desc(), ScoreSnapshot.id.desc()).first()
    if payload.get("scored_at") and historical_base is None and not all(
        key in payload for key in ("fit_score", "intent_score", "engagement_score")
    ):
        raise HTTPException(422, "No score snapshot exists at that timestamp. Supply all three score components for an independent historical calculation.")
    base_fit = historical_base.fit_score if historical_base else lead.fit_score
    base_intent = historical_base.intent_score if historical_base else lead.intent_score
    base_engagement = historical_base.engagement_score if historical_base else lead.engagement_score
    fit = float(payload.get("fit_score", base_fit))
    intent = float(payload.get("intent_score", base_intent))
    engagement = float(payload.get("engagement_score", base_engagement))
    if any(x < 0 or x > 100 for x in (fit, intent, engagement)):
        raise HTTPException(422, "Scores must be between 0 and 100")

    score, explanation = calculate_score(fit, intent, engagement, db)
    # Report later events explicitly; the historical snapshot above prevents them
    # from being inherited into this backdated score.
    future_activity_count = db.query(Activity).filter(
        Activity.lead_id == lead.id, Activity.occurred_at > scored_at
    ).count()
    explanation["scoring_timestamp"] = scored_at.isoformat()
    explanation["future_activities_excluded"] = future_activity_count
    if not is_historical:
        lead.fit_score, lead.intent_score = fit, intent
        lead.engagement_score, lead.total_score = engagement, score
        lead.score_explanation = explanation
    save_score_snapshot(db, lead, explanation, scored_at)
    db.add(Activity(
        lead_id=lead.id, activity_type="Lead Rescored",
        description=f"Score recalculated to {score}. Components: {explanation}",
        occurred_at=datetime.utcnow()
    ))
    db.commit()
    db.refresh(lead)
    response = lead_dict(lead, db)
    response["calculated_score"] = score
    response["historical_snapshot_only"] = is_historical
    return response


@router.get("/leads/{lead_id}/scores")
def lead_score_history(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    rows = db.query(ScoreSnapshot).filter(
        ScoreSnapshot.lead_id == lead_id
    ).order_by(ScoreSnapshot.scored_at.desc(), ScoreSnapshot.id.desc()).limit(100).all()
    return [{
        "scored_at": row.scored_at.isoformat(),
        "fit_score": row.fit_score,
        "intent_score": row.intent_score,
        "engagement_score": row.engagement_score,
        "total_score": row.total_score,
        "explanation": row.explanation,
    } for row in rows]


@router.patch("/leads/{lead_id}/consent")
def update_consent(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    status = str(payload.get("status", "")).lower()
    if status not in ("granted", "denied", "unknown"):
        raise HTTPException(422, "Invalid consent status")
    purpose = str(payload.get("purpose", "marketing")).strip().lower()
    if not purpose:
        raise HTTPException(422, "Consent purpose is required")
    if purpose == "marketing":
        lead.consent_status = status
    db.add(Consent(
        lead_id=lead.id, purpose=purpose,
        status=status, source=payload.get("source", "Manual")
    ))
    db.add(Activity(
        lead_id=lead.id, activity_type="Consent Updated",
        description=f"{payload.get('purpose', 'marketing')} consent changed to {status}"
    ))
    db.commit()
    return {"message": "Consent recorded", "lead_id": lead.id, "status": status}


@router.post("/leads/{lead_id}/activities", status_code=201)
def add_activity(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    kind = str(payload.get("activity_type", "Note")).strip()
    validate_marketing_consent(db, lead, kind)
    occurred_at = datetime.fromisoformat(payload["occurred_at"]) if payload.get("occurred_at") else datetime.utcnow()
    if occurred_at.tzinfo is not None:
        occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.utcnow()
    is_future = occurred_at > now
    won_history = db.query(StageHistory).join(Opportunity).filter(
        Opportunity.lead_id == lead.id, StageHistory.to_stage == "Won"
    ).order_by(StageHistory.changed_at.asc()).first()
    post_conversion = bool(won_history and occurred_at > won_history.changed_at)

    activity = Activity(
        lead_id=lead.id, activity_type=kind,
        description=payload.get("description", ""),
        metadata_json=payload.get("metadata", {}),
        occurred_at=occurred_at,
    )
    db.add(activity)

    score_eligible = not is_future and not post_conversion
    score_activity_types = ("email opened", "website visit", "demo requested", "form submitted", "webinar attended", "brochure downloaded", "pricing page visited")
    if score_eligible:
        lead.last_activity_at = max(filter(None, [lead.last_activity_at, occurred_at]), default=occurred_at)
        if kind.lower() in score_activity_types:
            lead.engagement_score = min(100, lead.engagement_score + 8)
            score, explanation = calculate_score(lead.fit_score, lead.intent_score, lead.engagement_score, db)
            lead.total_score, lead.score_explanation = score, explanation
            explanation = dict(explanation)
            explanation["scoring_timestamp"] = now.isoformat()
            save_score_snapshot(db, lead, explanation, now)

    db.commit()
    return {
        "message": "Activity recorded",
        "activity_id": activity.id,
        "lead_score": lead.total_score,
        "score_updated": bool(score_eligible and kind.lower() in score_activity_types),
        "excluded_from_scoring_reason": "FUTURE_DATED_ACTIVITY" if is_future else "POST_CONVERSION_ACTIVITY" if post_conversion else None,
    }


# ============================================================
# SALES REPS
# ============================================================

@router.get("/reps")
def list_reps(db: Session = Depends(get_db)):
    reps = db.query(SalesRep).order_by(SalesRep.name).all()
    return [{
        "id": r.id, "name": r.name, "email": r.email,
        "territory": r.territory, "active": r.active,
        "assigned_leads": db.query(Lead).filter(
            Lead.assigned_rep_id == r.id
        ).count()
    } for r in reps]


@router.get("/leads/{lead_id}/routing")
def preview_lead_routing(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    rep = matching_rep(db, lead.territory)
    return {
        "lead_id": lead.id,
        "territory": lead.territory,
        "assigned_rep_id": rep.id if rep else None,
        "assigned_rep": rep.name if rep else None,
        "routable": rep is not None,
        "reason": None if rep else "NO_ACTIVE_REPRESENTATIVE_FOR_TERRITORY",
    }


@router.patch("/leads/{lead_id}/assignment")
def assign_lead(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    rep = db.get(SalesRep, payload.get("assigned_rep_id"))
    if not rep or not rep.active:
        raise HTTPException(422, "Assigned representative must exist and be active")
    if (rep.territory or "").strip().lower() != (lead.territory or "").strip().lower():
        raise HTTPException(422, {
            "code": "TERRITORY_ROUTING_MISMATCH",
            "message": "Representative territory does not match lead territory",
            "lead_territory": lead.territory,
            "representative_territory": rep.territory,
        })
    lead.assigned_rep_id = rep.id
    db.commit()
    return {"message": "Lead assigned", "lead_id": lead.id, "assigned_rep_id": rep.id}


@router.post("/reps", status_code=201)
def create_rep(payload: dict, db: Session = Depends(get_db)):
    if not payload.get("name") or not payload.get("territory"):
        raise HTTPException(422, "Name and territory are required")
    rep = SalesRep(
        name=payload["name"], email=payload.get("email"),
        territory=payload["territory"]
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return {"id": rep.id, "name": rep.name, "territory": rep.territory}


# ============================================================
# TASKS
# ============================================================

@router.get("/tasks")
def list_tasks(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    rows = query.order_by(Task.due_at.asc()).limit(300).all()
    return [{
        "id": t.id, "public_id": t.public_id, "lead_id": t.lead_id,
        "lead_name": db.get(Lead, t.lead_id).name if db.get(Lead, t.lead_id) else "",
        "assigned_rep_id": t.assigned_rep_id, "title": t.title,
        "description": t.description, "due_at": t.due_at.isoformat() if t.due_at else None,
        "priority": t.priority, "status": t.status
    } for t in rows]


@router.post("/tasks", status_code=201)
def create_task(payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, payload.get("lead_id"))
    if not lead:
        raise HTTPException(404, "Lead not found")
    title = str(payload.get("title", "Follow up with lead")).strip()
    description = payload.get("description", "")
    validate_marketing_consent(db, lead, f"{title} {description}")
    rep_id = payload.get("assigned_rep_id", lead.assigned_rep_id)
    rep = db.get(SalesRep, rep_id) if rep_id else None
    if rep_id and (not rep or not rep.active):
        raise HTTPException(422, "Task representative must exist and be active")
    if rep and (rep.territory or "").strip().lower() != (lead.territory or "").strip().lower():
        raise HTTPException(422, "Task representative territory must match lead territory")
    task = Task(
        public_id="PENDING", lead_id=lead.id,
        assigned_rep_id=rep_id,
        title=title,
        description=description,
        due_at=datetime.fromisoformat(payload["due_at"]) if payload.get("due_at") else datetime.utcnow() + timedelta(days=1),
        priority=payload.get("priority", "Medium")
    )
    db.add(task)
    db.flush()
    task.public_id = f"TASK-{lead.public_id}-{task.id:03d}"
    db.commit()
    db.refresh(task)
    return {"id": task.id, "public_id": task.public_id, "status": task.status}


@router.patch("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = "Completed"
    task.completed_at = datetime.utcnow()
    db.commit()
    return {"message": "Task completed", "task_id": task.id}


# ============================================================
# OPPORTUNITIES AND AUDITABLE STAGE HISTORY
# ============================================================

@router.get("/opportunities")
def list_opportunities(db: Session = Depends(get_db)):
    rows = db.query(Opportunity).order_by(Opportunity.created_at.desc()).all()
    return [{
        "id": o.id, "public_id": o.public_id, "lead_id": o.lead_id,
        "lead_name": db.get(Lead, o.lead_id).name if db.get(Lead, o.lead_id) else "",
        "name": o.name, "amount": o.amount, "stage": o.stage,
        "probability": o.probability,
        "expected_close_date": o.expected_close_date.isoformat() if o.expected_close_date else None
    } for o in rows]


@router.post("/leads/{lead_id}/opportunities", status_code=201)
def create_opportunity(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    existing = db.query(Opportunity).filter(Opportunity.lead_id == lead_id).first()
    if existing:
        raise HTTPException(409, {
            "message": "An opportunity already exists for this lead",
            "opportunity_id": existing.id
        })

    opp = Opportunity(
        public_id="PENDING",
        lead_id=lead_id,
        name=payload.get("name", f"{lead.name} - Opportunity"),
        amount=float(payload.get("amount", 0)),
        stage="Qualified",
        probability=20,
        expected_close_date=datetime.fromisoformat(payload["expected_close_date"]) if payload.get("expected_close_date") else datetime.utcnow() + timedelta(days=30)
    )
    db.add(opp)
    db.flush()
    opp.public_id = f"OPP-{datetime.utcnow().year}-{opp.id:06d}"
    db.add(StageHistory(
        opportunity_id=opp.id, from_stage=None,
        to_stage="Qualified", reason="Opportunity created from lead"
    ))
    lead.status = "Qualified"
    db.add(Activity(
        lead_id=lead.id, activity_type="Opportunity Created",
        description=f"Opportunity {opp.public_id} created"
    ))
    db.commit()
    db.refresh(opp)
    return {"id": opp.id, "public_id": opp.public_id, "stage": opp.stage}


@router.patch("/opportunities/{opportunity_id}/stage")
def change_stage(opportunity_id: int, payload: dict, db: Session = Depends(get_db)):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(404, "Opportunity not found")

    allowed = {
        "Qualified": ["Proposal", "Lost"],
        "Proposal": ["Negotiation", "Lost"],
        "Negotiation": ["Won", "Lost"],
    }
    new_stage = payload.get("stage")
    if new_stage not in allowed.get(opp.stage, []):
        raise HTTPException(422, f"Invalid transition from {opp.stage} to {new_stage}")

    if new_stage == "Lost" and not str(payload.get("reason", "")).strip():
        raise HTTPException(422, "A reason is required when an opportunity is marked Lost")
    previous = opp.stage
    opp.stage = new_stage
    opp.probability = {
        "Qualified": 20, "Proposal": 50,
        "Negotiation": 75, "Won": 100, "Lost": 0
    }[new_stage]
    opp.outcome_reason = payload.get("reason")
    db.add(StageHistory(
        opportunity_id=opp.id, from_stage=previous,
        to_stage=new_stage, reason=payload.get("reason")
    ))
    db.commit()
    return {"message": "Stage updated", "from": previous, "to": new_stage}


@router.get("/opportunities/{opportunity_id}/history")
def opportunity_history(opportunity_id: int, db: Session = Depends(get_db)):
    if not db.get(Opportunity, opportunity_id):
        raise HTTPException(404, "Opportunity not found")
    rows = db.query(StageHistory).filter(
        StageHistory.opportunity_id == opportunity_id
    ).order_by(StageHistory.changed_at.asc()).all()
    return [{
        "from_stage": h.from_stage, "to_stage": h.to_stage,
        "reason": h.reason, "changed_at": h.changed_at.isoformat()
    } for h in rows]


# ============================================================
# DEMO DATA
# ============================================================

@router.post("/demo/seed")
def seed_demo_data(db: Session = Depends(get_db)):
    if db.query(Lead).count() > 0:
        return {"message": "Existing leads detected; seed skipped",
                "lead_count": db.query(Lead).count()}

    if not db.query(ScoreRule).first():
        db.add(ScoreRule(name="Default Lead Score", fit_weight=40,
                         intent_weight=35, engagement_weight=25))
    territories = ["North", "South", "East", "West"]
    reps = []
    for i, territory in enumerate(territories):
        rep = SalesRep(
            name=["Aarav Sharma", "Priya Reddy", "Rahul Mehta", "Ananya Das"][i],
            email=f"rep{i+1}@nexlead.demo", territory=territory
        )
        db.add(rep)
        reps.append(rep)
    db.flush()

    sources = ["Website", "LinkedIn", "Referral", "Campaign", "Webinar"]
    industries = ["Technology", "Finance", "Healthcare", "Retail", "Education"]
    random.seed(20261022)

    for i in range(1, 61):
        territory = territories[(i - 1) % 4]
        company = Company(
            name=f"{['Nexora','Vertex','Apex','Bluewave','Quantum'][i % 5]} "
                 f"{['Systems','Technologies','Solutions','Group'][i % 4]} {i}",
            industry=industries[i % 5], territory=territory
        )
        db.add(company)
        db.flush()

        name = f"{['Alex','Jordan','Taylor','Morgan','Casey'][i % 5]} Contact {i}"
        email = f"contact{i}@example.demo"
        contact = Contact(
            company_id=company.id, name=name, email=email,
            job_title=["CTO", "Marketing Manager", "Founder", "Director"][i % 4]
        )
        db.add(contact)
        db.flush()

        fit = random.randint(25, 100)
        intent = random.randint(15, 100)
        engagement = random.randint(10, 100)
        score, explanation = calculate_score(fit, intent, engagement, db)

        lead = Lead(
            public_id=f"LEAD-2026-{i:06d}",
            company_id=company.id, contact_id=contact.id,
            assigned_rep_id=reps[(i - 1) % 4].id,
            name=name, email=email, source=sources[i % 5],
            territory=territory, status="New",
            fit_score=fit, intent_score=intent,
            engagement_score=engagement, total_score=score,
            score_explanation=explanation,
            consent_status="denied" if i % 17 == 0 else "granted"
        )
        db.add(lead)
        db.flush()

        db.add(Consent(
            lead_id=lead.id, purpose="marketing",
            status=lead.consent_status, source="Demo Dataset"
        ))
        db.add(Activity(
            lead_id=lead.id, activity_type="Lead Created",
            description="Generated deterministic demo lead"
        ))

        if i % 3 == 0:
            db.add(Task(
                public_id=f"TASK-{i:06d}", lead_id=lead.id,
                assigned_rep_id=lead.assigned_rep_id,
                title="Follow up with prospect",
                due_at=datetime.utcnow() + timedelta(days=i % 7),
                priority="High" if score >= 75 else "Medium"
            ))

        if i % 5 == 0:
            stage = ["Qualified", "Proposal", "Negotiation", "Won", "Lost"][(i // 5) % 5]
            opp = Opportunity(
                public_id=f"OPP-2026-{i:06d}", lead_id=lead.id,
                name=f"{company.name} - Sales Opportunity",
                amount=random.choice([5000, 12000, 25000, 50000]),
                stage=stage,
                probability={"Qualified": 20, "Proposal": 50,
                             "Negotiation": 75, "Won": 100, "Lost": 0}[stage]
            )
            db.add(opp)
            db.flush()
            db.add(StageHistory(
                opportunity_id=opp.id, from_stage=None,
                to_stage="Qualified", reason="Initial qualification"
            ))
            if stage != "Qualified":
                db.add(StageHistory(
                    opportunity_id=opp.id, from_stage="Qualified",
                    to_stage=stage, reason="Demo outcome"
                ))

    db.commit()
    return {
        "message": "Demo dataset generated",
        "leads": db.query(Lead).count(),
        "companies": db.query(Company).count(),
        "contacts": db.query(Contact).count(),
        "sales_reps": db.query(SalesRep).count(),
        "tasks": db.query(Task).count(),
        "opportunities": db.query(Opportunity).count()
    }
