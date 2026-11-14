"""Additive NexLead hackathon extensions.

This module imports the existing CRM models and adds separate tables/routes.
It does not alter or delete existing CRM tables or records.
"""
from datetime import datetime, timedelta
import csv
import io
import random
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Session

from app.core.database import Base, get_db
from app import crm

router = APIRouter(tags=["NexLead Intelligence Extensions"])

Lead = crm.Lead
Company = crm.Company
Contact = crm.Contact
SalesRep = crm.SalesRep
Opportunity = crm.Opportunity
StageHistory = crm.StageHistory


class RepProduct(Base):
    __tablename__ = "sales_rep_products"
    __table_args__ = (UniqueConstraint("rep_id", "product_code", name="uq_rep_product"),)
    id = Column(Integer, primary_key=True)
    rep_id = Column(Integer, ForeignKey("sales_reps.id"), nullable=False, index=True)
    product_code = Column(String(80), nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)


class LeadProduct(Base):
    __tablename__ = "lead_products"
    __table_args__ = (UniqueConstraint("lead_id", "product_code", name="uq_lead_product"),)
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    product_code = Column(String(80), nullable=False, index=True)


class LeadGroundTruth(Base):
    __tablename__ = "lead_ground_truth"
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, unique=True, index=True)
    actual_converted = Column(Boolean, nullable=False, default=False)
    actual_won = Column(Boolean, nullable=False, default=False)
    ideal_rep_id = Column(Integer, ForeignKey("sales_reps.id"))
    duplicate_group = Column(String(80))
    injected_edge_case = Column(String(80))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _clean_code(value):
    code = str(value or "").strip().upper()
    if not code or len(code) > 80:
        raise HTTPException(422, "A product_code between 1 and 80 characters is required")
    return code


def _lead_or_404(db, lead_id):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


def _product_codes(db, lead_id):
    return [x.product_code for x in db.query(LeadProduct).filter(
        LeadProduct.lead_id == lead_id
    ).order_by(LeadProduct.product_code).all()]


def _eligible_reps(db, territory, product_code):
    q = db.query(SalesRep).join(
        RepProduct, RepProduct.rep_id == SalesRep.id
    ).filter(
        SalesRep.active.is_(True),
        RepProduct.active.is_(True),
        func.lower(SalesRep.territory) == str(territory or "").strip().lower(),
        func.lower(RepProduct.product_code) == product_code.lower(),
    )
    return q.order_by(SalesRep.id).all()


@router.put("/reps/{rep_id}/products")
def set_rep_products(rep_id: int, payload: dict, db: Session = Depends(get_db)):
    rep = db.get(SalesRep, rep_id)
    if not rep:
        raise HTTPException(404, "Sales representative not found")
    products = payload.get("product_codes")
    if not isinstance(products, list) or not products:
        raise HTTPException(422, "product_codes must be a non-empty list")
    codes = sorted(set(_clean_code(x) for x in products))
    db.query(RepProduct).filter(RepProduct.rep_id == rep_id).delete(synchronize_session=False)
    db.add_all([RepProduct(rep_id=rep_id, product_code=x, active=True) for x in codes])
    db.commit()
    return {"rep_id": rep_id, "product_codes": codes}


@router.get("/reps/{rep_id}/products")
def get_rep_products(rep_id: int, db: Session = Depends(get_db)):
    if not db.get(SalesRep, rep_id):
        raise HTTPException(404, "Sales representative not found")
    codes = [x.product_code for x in db.query(RepProduct).filter(
        RepProduct.rep_id == rep_id, RepProduct.active.is_(True)
    ).order_by(RepProduct.product_code).all()]
    return {"rep_id": rep_id, "product_codes": codes}


@router.put("/leads/{lead_id}/products")
def set_lead_products(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    _lead_or_404(db, lead_id)
    products = payload.get("product_codes")
    if not isinstance(products, list) or not products:
        raise HTTPException(422, "product_codes must be a non-empty list")
    codes = sorted(set(_clean_code(x) for x in products))
    db.query(LeadProduct).filter(LeadProduct.lead_id == lead_id).delete(synchronize_session=False)
    db.add_all([LeadProduct(lead_id=lead_id, product_code=x) for x in codes])
    db.commit()
    return {"lead_id": lead_id, "product_codes": codes}


@router.get("/leads/{lead_id}/product-routing")
def product_routing_preview(lead_id: int, product_code: str = Query(...), db: Session = Depends(get_db)):
    lead = _lead_or_404(db, lead_id)
    code = _clean_code(product_code)
    reps = _eligible_reps(db, lead.territory, code)
    selected = reps[0] if reps else None
    return {
        "lead_id": lead.id,
        "territory": lead.territory,
        "product_code": code,
        "eligible_representatives": len(reps),
        "assigned_rep_id": selected.id if selected else None,
        "assigned_rep": selected.name if selected else None,
        "routable": selected is not None,
        "reason": None if selected else "NO_ACTIVE_REP_FOR_TERRITORY_AND_PRODUCT",
    }


@router.patch("/leads/{lead_id}/product-assignment")
def assign_product_lead(lead_id: int, payload: dict, db: Session = Depends(get_db)):
    lead = _lead_or_404(db, lead_id)
    code = _clean_code(payload.get("product_code"))
    rep_id = payload.get("assigned_rep_id")
    rep = db.get(SalesRep, rep_id) if rep_id else None
    if not rep or not rep.active:
        raise HTTPException(422, "Representative must exist and be active")
    if (rep.territory or "").strip().lower() != (lead.territory or "").strip().lower():
        raise HTTPException(422, {"code": "TERRITORY_ROUTING_MISMATCH"})
    eligible = _eligible_reps(db, lead.territory, code)
    if rep.id not in {x.id for x in eligible}:
        raise HTTPException(422, {"code": "PRODUCT_SPECIALTY_MISMATCH", "product_code": code})
    lead.assigned_rep_id = rep.id
    exists = db.query(LeadProduct).filter(
        LeadProduct.lead_id == lead.id, LeadProduct.product_code == code
    ).first()
    if not exists:
        db.add(LeadProduct(lead_id=lead.id, product_code=code))
    db.commit()
    return {"message": "Product-qualified lead assigned", "lead_id": lead.id,
            "assigned_rep_id": rep.id, "product_code": code}


@router.get("/duplicates/review")
def duplicate_review(limit: int = Query(5000, ge=1, le=20000), db: Session = Depends(get_db)):
    """Find likely duplicates; this is review-only and never merges/deletes records."""
    rows = db.query(Lead).order_by(Lead.id).limit(limit).all()
    buckets = {}
    for lead in rows:
        email = (lead.email or "").strip().lower()
        name = " ".join((lead.name or "").lower().split())
        company = db.get(Company, lead.company_id) if lead.company_id else None
        company_name = " ".join((company.name if company else "").lower().split())
        key = ("email", email) if email else ("name_company", name, company_name)
        if (email or name) and key not in buckets:
            buckets[key] = []
        if email or name:
            buckets[key].append({"lead_id": lead.id, "public_id": lead.public_id,
                                 "name": lead.name, "email": lead.email,
                                 "company": company.name if company else None})
    groups = [items for items in buckets.values() if len(items) > 1]
    return {"scanned_leads": len(rows), "duplicate_groups": len(groups),
            "possible_duplicates": groups}


@router.post("/data/generate")
def generate_labelled_data(
    lead_count: int = Query(500, ge=1, le=20000),
    seed: int = Query(20261114),
    db: Session = Depends(get_db),
):
    """Append deterministic synthetic leads with isolated ground-truth labels."""
    rng = random.Random(seed)
    territories = ["North", "South", "East", "West"]
    industries = ["Technology", "Finance", "Healthcare", "Retail", "Education"]
    sources = ["Website", "LinkedIn", "Referral", "Webinar", "Partner"]
    products = ["CRM", "ANALYTICS", "AUTOMATION"]
    reps = db.query(SalesRep).filter(SalesRep.active.is_(True)).order_by(SalesRep.id).all()
    if not reps:
        raise HTTPException(409, "Create at least one active sales representative first")

    # Give each existing rep deterministic product coverage only when no mapping exists.
    for idx, rep in enumerate(reps):
        if not db.query(RepProduct).filter(RepProduct.rep_id == rep.id).first():
            db.add_all([RepProduct(rep_id=rep.id, product_code=products[(idx + j) % len(products)])
                        for j in range(2)])
    db.flush()

    created = 0
    edge_counts = Counter()
    start_id = (db.query(func.coalesce(func.max(Lead.id), 0)).scalar() or 0) + 1
    year = datetime.utcnow().year
    for i in range(lead_count):
        territory = territories[i % len(territories)]
        matching = [r for r in reps if (r.territory or "").lower() == territory.lower()]
        rep = matching[i % len(matching)] if matching else reps[i % len(reps)]
        product = products[i % len(products)]
        company_no = start_id + i
        company = Company(
            name=f"NexLead Synthetic {seed} Company {company_no}",
            industry=industries[i % len(industries)], territory=territory,
        )
        db.add(company)
        db.flush()
        person_name = f"Synthetic Contact {company_no}"
        email = f"synthetic.{seed}.{company_no}@example.invalid"
        contact = Contact(company_id=company.id, name=person_name, email=email,
                          job_title=["Founder", "Director", "CTO"][i % 3])
        db.add(contact)
        db.flush()

        fit, intent, engagement = (rng.randint(20, 100), rng.randint(10, 100), rng.randint(5, 100))
        score, explanation = crm.calculate_score(fit, intent, engagement, db)
        actual_converted = (i % 4 != 0)
        actual_won = actual_converted and (i % 5 == 0)
        edge = None
        if i % 23 == 0:
            edge = "LOW_SCORE_CONVERTED"
        elif i % 29 == 0:
            edge = "HIGH_SCORE_NOT_CONVERTED"
        elif i % 31 == 0:
            edge = "MARKETING_CONSENT_DENIED"
        lead = Lead(
            public_id=f"LEAD-{year}-{company_no:06d}", company_id=company.id,
            contact_id=contact.id, assigned_rep_id=rep.id,
            name=person_name, email=email, source=sources[i % len(sources)],
            territory=territory, status="Qualified" if actual_converted else "New",
            fit_score=fit, intent_score=intent, engagement_score=engagement,
            total_score=score, score_explanation=explanation,
            consent_status="denied" if edge == "MARKETING_CONSENT_DENIED" else "granted",
        )
        db.add(lead)
        db.flush()
        db.add(LeadProduct(lead_id=lead.id, product_code=product))
        db.add(LeadGroundTruth(
            lead_id=lead.id, actual_converted=actual_converted, actual_won=actual_won,
            ideal_rep_id=rep.id, duplicate_group=None, injected_edge_case=edge,
        ))
        if edge:
            edge_counts[edge] += 1
        created += 1
        if created % 250 == 0:
            db.flush()

    db.commit()
    return {"message": "Synthetic dataset appended", "created_leads": created,
            "seed": seed, "ground_truth_labels": created, "edge_cases": dict(edge_counts),
            "total_leads": db.query(Lead).count()}


@router.get("/evaluation/metrics")
def evaluation_metrics(db: Session = Depends(get_db)):
    rows = db.query(Lead, LeadGroundTruth).join(
        LeadGroundTruth, LeadGroundTruth.lead_id == Lead.id
    ).all()
    if not rows:
        return {"labelled_records": 0, "message": "Generate labelled data first"}
    # A transparent baseline classifier: score >= 60 predicts conversion.
    tp = fp = tn = fn = 0
    routing_total = routing_correct = 0
    for lead, truth in rows:
        predicted = lead.total_score >= 60
        actual = bool(truth.actual_converted)
        if predicted and actual: tp += 1
        elif predicted and not actual: fp += 1
        elif not predicted and not actual: tn += 1
        else: fn += 1
        if truth.ideal_rep_id is not None:
            routing_total += 1
            if lead.assigned_rep_id == truth.ideal_rep_id:
                routing_correct += 1
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    accuracy = (tp + tn) / len(rows)
    return {
        "labelled_records": len(rows),
        "classifier": "Baseline score threshold >= 60",
        "confusion_matrix": {"true_positive": tp, "false_positive": fp,
                             "true_negative": tn, "false_negative": fn},
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round((2 * precision * recall / (precision + recall)) if precision + recall else 0, 4),
        "routing_accuracy": round(routing_correct / routing_total, 4) if routing_total else None,
        "routing_evaluated": routing_total,
        "warning": "Metrics describe only records with generated ground-truth labels; the score threshold is a baseline, not a trained model.",
    }


@router.get("/data/export.csv")
def export_labelled_data(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["lead_id", "public_id", "name", "email", "territory",
                     "assigned_rep_id", "fit_score", "intent_score", "engagement_score",
                     "total_score", "product_codes", "actual_converted", "actual_won",
                     "ideal_rep_id", "injected_edge_case"])
    rows = db.query(Lead, LeadGroundTruth).join(
        LeadGroundTruth, LeadGroundTruth.lead_id == Lead.id
    ).order_by(Lead.id).all()
    for lead, truth in rows:
        writer.writerow([lead.id, lead.public_id, lead.name, lead.email, lead.territory,
                         lead.assigned_rep_id, lead.fit_score, lead.intent_score,
                         lead.engagement_score, lead.total_score,
                         ";".join(_product_codes(db, lead.id)),
                         int(truth.actual_converted), int(truth.actual_won),
                         truth.ideal_rep_id, truth.injected_edge_case or ""])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=nexlead_labelled_data.csv"})
