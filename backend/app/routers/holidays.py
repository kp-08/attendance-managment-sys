from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

router = APIRouter(prefix="/holidays", tags=["holidays"])

@router.post("/create")
def create_holiday(payload: schemas.HolidayCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only admin can create holidays")
    h = models.Holiday(name=payload.name, date=payload.date, description=payload.description)
    db.add(h)
    db.commit()
    db.refresh(h)
    return h

@router.get("/list")
def list_holidays(db: Session = Depends(get_db)):
    return db.query(models.Holiday).order_by(models.Holiday.date).all()
