import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin_user, get_current_user, get_db
from app.models.rules import PointRule, RuleSet, SelectionRule, SeriesRuleSet
from app.models.user import User
from app.schemas.rules import RuleSetCreate, RuleSetResponse

router = APIRouter(prefix="/rule-sets", tags=["rules"])


@router.get("", response_model=list[RuleSetResponse])
def list_rule_sets(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(RuleSet).all()


@router.get("/{rule_set_id}", response_model=RuleSetResponse)
def get_rule_set(rule_set_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rs = db.query(RuleSet).filter(RuleSet.id == rule_set_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return rs


@router.post("", response_model=RuleSetResponse, status_code=status.HTTP_201_CREATED)
def create_rule_set(
    body: RuleSetCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    rs = RuleSet(name=body.name, description=body.description, is_active=body.is_active)
    db.add(rs)
    db.flush()
    for pr in body.point_rules:
        db.add(PointRule(rule_set_id=rs.id, **pr.model_dump()))
    for sr in body.selection_rules:
        db.add(SelectionRule(rule_set_id=rs.id, **sr.model_dump()))
    db.commit()
    db.refresh(rs)
    return rs


@router.delete("/{rule_set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule_set(
    rule_set_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    rs = db.query(RuleSet).filter(RuleSet.id == rule_set_id).first()
    if not rs:
        raise HTTPException(status_code=404, detail="Rule set not found")
    db.delete(rs)
    db.commit()


@router.post("/{rule_set_id}/assign-series/{series_id}", status_code=status.HTTP_200_OK)
def assign_to_series(
    rule_set_id: uuid.UUID,
    series_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    existing = db.query(SeriesRuleSet).filter(
        SeriesRuleSet.series_id == series_id, SeriesRuleSet.rule_set_id == rule_set_id
    ).first()
    if not existing:
        db.add(SeriesRuleSet(series_id=series_id, rule_set_id=rule_set_id))
        db.commit()
    return {"message": "Assigned"}
