"""Additive campaign management and lead attribution endpoints.

Uses the existing Campaign, LeadCampaign, Lead and Opportunity models.
No schema changes or migrations are required.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app import crm

router = APIRouter(tags=["Campaign Management"])
get_db = crm.get_db
Campaign = crm.Campaign
LeadCampaign = crm.LeadCampaign
Lead = crm.Lead
Opportunity = crm.Opportunity


def _campaign_or_404(db: Session, campaign_id: int):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


def _campaign_summary(db: Session, campaign: Campaign):
    lead_ids = db.query(LeadCampaign.lead_id).filter(
        LeadCampaign.campaign_id == campaign.id
    ).subquery()

    attributed_leads = db.query(func.count(distinct(LeadCampaign.lead_id))).filter(
        LeadCampaign.campaign_id == campaign.id
    ).scalar() or 0

    opportunities = db.query(Opportunity).filter(
        Opportunity.lead_id.in_(lead_ids)
    ).all()

    won = [o for o in opportunities if o.stage == "Won"]
    lost = [o for o in opportunities if o.stage == "Lost"]
    open_opps = [o for o in opportunities if o.stage not in ("Won", "Lost")]

    won_revenue = round(sum(float(o.amount or 0) for o in won), 2)
    pipeline_value = round(sum(float(o.amount or 0) for o in open_opps), 2)
    decided = len(won) + len(lost)

    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "channel": campaign.channel,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "attributed_leads": attributed_leads,
        "opportunities": len(opportunities),
        "won_opportunities": len(won),
        "lost_opportunities": len(lost),
        "open_opportunities": len(open_opps),
        "win_rate": round((len(won) / decided) * 100, 2) if decided else 0.0,
        "won_revenue": won_revenue,
        "open_pipeline_value": pipeline_value,
        "roi": None,
        "roi_note": "Not calculable: campaign budget/cost is not stored in the current schema."
    }


@router.post("/campaigns", status_code=201)
def create_campaign(payload: dict, db: Session = Depends(get_db)):
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Campaign name is required")
    status = str(payload.get("status") or "active").strip().lower()
    if status not in {"active", "paused", "completed", "archived"}:
        raise HTTPException(status_code=422, detail="Invalid campaign status")
    campaign = Campaign(
        name=name,
        channel=(str(payload.get("channel") or "Other").strip() or "Other"),
        status=status
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _campaign_summary(db, campaign)


@router.get("/campaigns")
def list_campaigns(
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Campaign)
    if status:
        query = query.filter(func.lower(Campaign.status) == status.strip().lower())
    campaigns = query.order_by(Campaign.created_at.desc(), Campaign.id.desc()).all()
    return {
        "count": len(campaigns),
        "campaigns": [_campaign_summary(db, c) for c in campaigns]
    }


@router.get("/campaigns/analytics")
def campaign_analytics(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).order_by(Campaign.id.asc()).all()
    summaries = [_campaign_summary(db, c) for c in campaigns]
    return {
        "campaign_count": len(summaries),
        "total_attributed_leads": sum(x["attributed_leads"] for x in summaries),
        "total_opportunities": sum(x["opportunities"] for x in summaries),
        "total_won_opportunities": sum(x["won_opportunities"] for x in summaries),
        "total_won_revenue": round(sum(x["won_revenue"] for x in summaries), 2),
        "campaigns": summaries,
        "roi_note": "ROI is unavailable until campaign spend is captured."
    }


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_or_404(db, campaign_id)
    return _campaign_summary(db, campaign)


@router.patch("/campaigns/{campaign_id}")
def update_campaign(campaign_id: int, payload: dict, db: Session = Depends(get_db)):
    campaign = _campaign_or_404(db, campaign_id)

    if "name" in payload:
        name = str(payload["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Campaign name cannot be empty")
        campaign.name = name

    if "channel" in payload:
        campaign.channel = str(payload["channel"] or "Other").strip() or "Other"

    if "status" in payload:
        status = str(payload["status"] or "").strip().lower()
        if status not in {"active", "paused", "completed", "archived"}:
            raise HTTPException(status_code=422, detail="Invalid campaign status")
        campaign.status = status

    db.commit()
    db.refresh(campaign)
    return _campaign_summary(db, campaign)


@router.post("/campaigns/{campaign_id}/leads/{lead_id}", status_code=201)
def attribute_lead(campaign_id: int, lead_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_or_404(db, campaign_id)
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    existing = db.query(LeadCampaign).filter(
        LeadCampaign.campaign_id == campaign_id,
        LeadCampaign.lead_id == lead_id
    ).first()
    if existing:
        return {
            "message": "Lead is already attributed to this campaign",
            "campaign_id": campaign_id,
            "lead_id": lead_id,
            "linked_at": existing.linked_at.isoformat() if existing.linked_at else None,
            "already_linked": True
        }

    link = LeadCampaign(
        campaign_id=campaign.id,
        lead_id=lead.id,
        linked_at=datetime.utcnow()
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {
        "message": "Lead attributed to campaign",
        "campaign_id": campaign.id,
        "lead_id": lead.id,
        "linked_at": link.linked_at.isoformat() if link.linked_at else None,
        "already_linked": False
    }


@router.delete("/campaigns/{campaign_id}/leads/{lead_id}")
def remove_lead_attribution(campaign_id: int, lead_id: int, db: Session = Depends(get_db)):
    _campaign_or_404(db, campaign_id)
    link = db.query(LeadCampaign).filter(
        LeadCampaign.campaign_id == campaign_id,
        LeadCampaign.lead_id == lead_id
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Campaign attribution not found")
    db.delete(link)
    db.commit()
    return {"message": "Lead attribution removed", "campaign_id": campaign_id, "lead_id": lead_id}


@router.get("/campaigns/{campaign_id}/leads")
def campaign_leads(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_or_404(db, campaign_id)
    rows = db.query(Lead, LeadCampaign).join(
        LeadCampaign, LeadCampaign.lead_id == Lead.id
    ).filter(
        LeadCampaign.campaign_id == campaign_id
    ).order_by(LeadCampaign.linked_at.desc()).all()

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.name,
        "count": len(rows),
        "leads": [{
            "lead_id": lead.id,
            "public_id": lead.public_id,
            "name": lead.name,
            "email": lead.email,
            "source": lead.source,
            "status": lead.status,
            "total_score": lead.total_score,
            "attributed_at": link.linked_at.isoformat() if link.linked_at else None
        } for lead, link in rows]
    }


@router.get("/campaigns/{campaign_id}/performance")
def campaign_performance(campaign_id: int, db: Session = Depends(get_db)):
    campaign = _campaign_or_404(db, campaign_id)
    return _campaign_summary(db, campaign)
