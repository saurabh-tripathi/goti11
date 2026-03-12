import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin_user, get_current_user, get_db
from app.models.series import Series
from app.models.user import User
from app.schemas.series import SeriesCreate, SeriesPatch, SeriesResponse

router = APIRouter(prefix="/series", tags=["series"])


@router.get("", response_model=list[SeriesResponse])
def list_series(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Series).order_by(Series.start_date.desc()).all()


@router.get("/{series_id}", response_model=SeriesResponse)
def get_series(series_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = db.query(Series).filter(Series.id == series_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Series not found")
    return s


@router.post("", response_model=SeriesResponse, status_code=status.HTTP_201_CREATED)
def create_series(
    body: SeriesCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    s = Series(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.patch("/{series_id}", response_model=SeriesResponse)
def patch_series(
    series_id: uuid.UUID,
    body: SeriesPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    s = db.query(Series).filter(Series.id == series_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Series not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s
