from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

from typing import Optional
from sqlalchemy import and_

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/check-in")
def check_in(db: Session = Depends(get_db), user = Depends(get_current_user)):
    today = date.today()
    # ensure unique per day
    rec = db.query(models.AttendanceRecord).filter_by(employee_id=user.id, date=today).first()
    now = datetime.utcnow()
    if rec:
        # if check_in already exists, return it
        if rec.check_in_time:
            raise HTTPException(status_code=400, detail="Already checked in today")
        rec.check_in_time = now
        db.commit()
        db.refresh(rec)
        return rec
    rec = models.AttendanceRecord(employee_id=user.id, date=today, check_in_time=now, status="PRESENT")
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

@router.post("/check-out")
def check_out(db: Session = Depends(get_db), user = Depends(get_current_user)):
    today = date.today()
    rec = db.query(models.AttendanceRecord).filter_by(employee_id=user.id, date=today).first()
    if not rec or not rec.check_in_time:
        raise HTTPException(status_code=400, detail="No check-in record found for today")
    if rec.check_out_time:
        raise HTTPException(status_code=400, detail="Already checked out")
    rec.check_out_time = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/list", response_model=schemas.AttendanceListResponse)
def list_attendance(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Optional[str] = None,
    order: str = "desc",
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Paginated attendance list with optional filtering and sorting.

    Default ordering is date DESC unless sort_by is provided.
    sort_by allowed: date, check_in_time, check_out_time
    order: asc | desc  (default desc)
    """
    allowed_sort_fields = {"date", "check_in_time", "check_out_time"}

    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")

    query = db.query(models.AttendanceRecord)

    # Scope by role
    if user.role == models.RoleEnum.employee:
        query = query.filter(models.AttendanceRecord.employee_id == user.id)
    else:
        if employee_id:
            query = query.filter(models.AttendanceRecord.employee_id == employee_id)

    # date range
    if start_date:
        query = query.filter(models.AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(models.AttendanceRecord.date <= end_date)

    # sorting
    if sort_by:
        if sort_by not in allowed_sort_fields:
            raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Allowed: {sorted(list(allowed_sort_fields))}")
        col = getattr(models.AttendanceRecord, sort_by)
        if order == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())
    else:
        # default
        query = query.order_by(models.AttendanceRecord.date.desc())

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": items}
