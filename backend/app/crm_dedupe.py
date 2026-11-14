"""Safe duplicate review and lead merge operations for NexLead.

The original lead is retained as a tombstone with status='Merged'.
Related operational records are transferred to the surviving lead.
A small audit table records the merge. Existing business tables are not dropped.
"""
from datetime import datetime
from typing import Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Session

from app import crm
from app.core.database import Base

router = APIRouter(tags=["Duplicate Management"])
get_db = crm.get_db

Lead = crm.Lead
Company = crm.Company
Contact = crm.Contact
LeadCampaign = crm.LeadCampaign
Activity = crm.Activity
Consent = crm.Consent
ScoreSnapshot = crm.ScoreSnapshot
Task = crm.Task
Opportunity = crm.Opportunity


class LeadMergeAudit(Base):
    __tablename__ = "lead_merge_audits"

    id = Column(Integer, primary_key=True)
    source_lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, unique=True)
    survivor_lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    merged_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=False)


def _norm(value):
    return " ".join((value or "").strip().casefold().split())


def _company_name(db, lead):
    if not lead.company_id:
        return ""
    company = db.get(Company, lead.company_id)
    return _norm(company.name) if company else ""


def _match_reason(db, a, b):
    ea, eb = _norm(a.email), _norm(b.email)
    if ea and eb and ea == eb:
        return "EXACT_EMAIL"
    na, nb = _norm(a.name), _norm(b.name)
    ca, cb = _company_name(db, a), _company_name(db, b)
    if na and na == nb and ca and ca == cb:
        return "EXACT_NAME_AND_COMPANY"
    return None


def _duplicate_groups(db):
    leads = db.query(Lead).filter(Lead.status != "Merged").order_by(Lead.id.asc()).all()
    buckets: Dict[Tuple[str, str], List[Lead]] = {}

    for lead in leads:
        email = _norm(lead.email)
        if email:
            buckets.setdefault(("email", email), []).append(lead)

        name = _norm(lead.name)
        company = _company_name(db, lead)
        if name and company:
            buckets.setdefault(("name_company", name + "|" + company), []).append(lead)

    groups = []
    seen = set()
    for (kind, key), members in buckets.items():
        if len(members) < 2:
            continue
        ids = tuple(sorted(x.id for x in members))
        marker = (kind, ids)
        if marker in seen:
            continue
        seen.add(marker)
        groups.append({
            "match_type": "EXACT_EMAIL" if kind == "email" else "EXACT_NAME_AND_COMPANY",
            "match_value": key if kind == "email" else None,
            "leads": [{
                "id": lead.id,
                "public_id": lead.public_id,
                "name": lead.name,
                "email": lead.email,
                "company_id": lead.company_id,
                "company_name": _company_name(db, lead),
                "territory": lead.territory,
                "status": lead.status,
                "total_score": lead.total_score,
                "created_at": lead.created_at.isoformat() if lead.created_at else None
            } for lead in members]
        })
    return groups


@router.get("/duplicates/candidates")
def duplicate_candidates(db: Session = Depends(get_db)):
    groups = _duplicate_groups(db)
    return {
        "group_count": len(groups),
        "candidate_pair_count": sum(len(g["leads"]) * (len(g["leads"]) - 1) // 2 for g in groups),
        "matching_rules": [
            "Exact normalized email",
            "Exact normalized lead name and company name"
        ],
        "groups": groups
    }


@router.post("/duplicates/merge")
def merge_duplicate_leads(payload: dict, db: Session = Depends(get_db)):
    source_id = payload.get("source_lead_id")
    survivor_id = payload.get("survivor_lead_id")
    reason_text = str(payload.get("reason") or "").strip()

    if not isinstance(source_id, int) or not isinstance(survivor_id, int):
        raise HTTPException(status_code=422, detail="source_lead_id and survivor_lead_id must be integers")
    if source_id == survivor_id:
        raise HTTPException(status_code=422, detail="Source and survivor must be different leads")
    if not reason_text:
        raise HTTPException(status_code=422, detail="A merge reason is required")

    source = db.get(Lead, source_id)
    survivor = db.get(Lead, survivor_id)
    if not source or not survivor:
        raise HTTPException(status_code=404, detail="Source or survivor lead not found")
    if source.status == "Merged":
        raise HTTPException(status_code=409, detail="Source lead has already been merged")
    if survivor.status == "Merged":
        raise HTTPException(status_code=409, detail="Survivor cannot be an already merged lead")

    prior = db.query(LeadMergeAudit).filter(
        LeadMergeAudit.source_lead_id == source_id
    ).first()
    if prior:
        raise HTTPException(status_code=409, detail={
            "message": "Source lead already has a merge audit",
            "survivor_lead_id": prior.survivor_lead_id
        })

    match_reason = _match_reason(db, source, survivor)
    if not match_reason:
        raise HTTPException(
            status_code=422,
            detail="Merge blocked: leads must share an exact normalized email or exact name and company."
        )

    moved = {}

    # Move campaign attributions, avoiding duplicate (lead, campaign) links.
    source_links = db.query(LeadCampaign).filter(LeadCampaign.lead_id == source_id).all()
    moved_campaigns = 0
    for link in source_links:
        exists = db.query(LeadCampaign).filter(
            LeadCampaign.lead_id == survivor_id,
            LeadCampaign.campaign_id == link.campaign_id
        ).first()
        if exists:
            db.delete(link)
        else:
            link.lead_id = survivor_id
            moved_campaigns += 1
    moved["campaign_attributions"] = moved_campaigns

    # Move records whose identity/history should follow the surviving lead.
    for model, label in [
        (Activity, "activities"),
        (Consent, "consent_records"),
        (ScoreSnapshot, "score_snapshots"),
        (Task, "tasks"),
        (Opportunity, "opportunities"),
    ]:
        count = db.query(model).filter(model.lead_id == source_id).update(
            {model.lead_id: survivor_id}, synchronize_session=False
        )
        moved[label] = count

    # Optional product mapping extension: preserve all distinct product codes.
    try:
        from app.crm_extensions import LeadProduct
        source_products = db.query(LeadProduct).filter(LeadProduct.lead_id == source_id).all()
        product_count = 0
        for item in source_products:
            exists = db.query(LeadProduct).filter(
                LeadProduct.lead_id == survivor_id,
                func.lower(LeadProduct.product_code) == item.product_code.lower()
            ).first()
            if exists:
                db.delete(item)
            else:
                item.lead_id = survivor_id
                product_count += 1
        moved["product_mappings"] = product_count
    except (ImportError, AttributeError):
        moved["product_mappings"] = 0

    # Move ground-truth label only if survivor has none. If both have labels,
    # retain the source label on the tombstone so no labelled record is destroyed.
    try:
        from app.crm_extensions import LeadGroundTruth
        source_truth = db.query(LeadGroundTruth).filter(
            LeadGroundTruth.lead_id == source_id
        ).first()
        survivor_truth = db.query(LeadGroundTruth).filter(
            LeadGroundTruth.lead_id == survivor_id
        ).first()
        if source_truth and not survivor_truth:
            source_truth.lead_id = survivor_id
            moved["ground_truth_label"] = "transferred"
        elif source_truth and survivor_truth:
            moved["ground_truth_label"] = "retained_on_merged_source_record"
        else:
            moved["ground_truth_label"] = "none"
    except (ImportError, AttributeError):
        moved["ground_truth_label"] = "not_configured"

    # Fill only missing survivor identity fields; never overwrite populated values.
    if not survivor.email and source.email:
        survivor.email = source.email
    if not survivor.contact_id and source.contact_id:
        survivor.contact_id = source.contact_id
    if not survivor.company_id and source.company_id:
        survivor.company_id = source.company_id
    if not survivor.assigned_rep_id and source.assigned_rep_id:
        survivor.assigned_rep_id = source.assigned_rep_id

    # Consent is conservative: an explicit denial must not be weakened by a merge.
    if (source.consent_status or "").lower() == "denied":
        survivor.consent_status = "denied"

    # Preserve the most recent activity timestamp.
    dates = [d for d in (source.last_activity_at, survivor.last_activity_at) if d]
    if dates:
        survivor.last_activity_at = max(dates)

    source.status = "Merged"
    source.updated_at = datetime.utcnow()

    db.add(LeadMergeAudit(
        source_lead_id=source_id,
        survivor_lead_id=survivor_id,
        reason=f"{match_reason}: {reason_text}"
    ))

    # Audit event is also visible in the surviving lead's activity timeline.
    db.add(Activity(
        lead_id=survivor_id,
        activity_type="Duplicate Merge",
        description=f"Lead {source.public_id} merged into {survivor.public_id}. Reason: {reason_text}",
        occurred_at=datetime.utcnow(),
        metadata_json={
            "source_lead_id": source_id,
            "source_public_id": source.public_id,
            "survivor_lead_id": survivor_id,
            "match_reason": match_reason,
            "moved_records": moved
        }
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Duplicate lead merged successfully",
        "source_lead_id": source_id,
        "source_public_id": source.public_id,
        "survivor_lead_id": survivor_id,
        "survivor_public_id": survivor.public_id,
        "match_reason": match_reason,
        "source_record_retained": True,
        "source_status": "Merged",
        "moved_records": moved,
        "note": "The source lead remains as a merged audit record; its company/contact master records are retained."
    }


@router.get("/duplicates/merge-audit")
def merge_audit(db: Session = Depends(get_db)):
    rows = db.query(LeadMergeAudit).order_by(LeadMergeAudit.merged_at.desc()).limit(200).all()
    return {
        "count": len(rows),
        "merges": [{
            "id": row.id,
            "source_lead_id": row.source_lead_id,
            "survivor_lead_id": row.survivor_lead_id,
            "merged_at": row.merged_at.isoformat() if row.merged_at else None,
            "reason": row.reason
        } for row in rows]
    }
