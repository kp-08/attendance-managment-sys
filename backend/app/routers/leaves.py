from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.database import get_db
from app import models, schemas
from app.deps import get_current_user

from sqlalchemy.exc import NoResultFound
from sqlalchemy import select

router = APIRouter(prefix="/leave", tags=["leave"])

@router.post("/apply", response_model=schemas.LeaveRequestOut)
def apply_leave(payload: schemas.LeaveRequestCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    # check dates
    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    lr = models.LeaveRequest(
        employee_id=user.id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status=models.LeaveStatus.pending
    )
    db.add(lr)
    db.commit()
    db.refresh(lr)
    return lr

@router.get("/list")
def list_leaves(db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role in (models.RoleEnum.admin, models.RoleEnum.manager):
        return db.query(models.LeaveRequest).order_by(models.LeaveRequest.applied_at.desc()).all()
    return db.query(models.LeaveRequest).filter_by(employee_id=user.id).order_by(models.LeaveRequest.applied_at.desc()).all()

@router.put("/{leave_id}/approve")
# Only admin/manager can approve
def approve_leave(leave_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role not in (models.RoleEnum.admin, models.RoleEnum.manager):
        raise HTTPException(status_code=403, detail="Only admin/manager can approve")

    lr = db.query(models.LeaveRequest).filter_by(id=leave_id).with_for_update().first()
    if not lr:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if lr.status != models.LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="Leave request not pending")

    requested_days = (lr.end_date - lr.start_date).days + 1
    year = lr.start_date.year

    # start transaction
    try:
        # lock or create balance row
        balance = db.query(models.LeaveBalance).filter_by(employee_id=lr.employee_id, year=year).with_for_update().first()
        if not balance:
            balance = models.LeaveBalance(employee_id=lr.employee_id, year=year, total_leaves=17, used_leaves=0, remaining_leaves=17)
            db.add(balance)
            db.flush()  # ensure we have the row and it's locked

        if balance.remaining_leaves < requested_days:
            raise HTTPException(status_code=400, detail=f"Insufficient leave balance (remaining {balance.remaining_leaves})")

        # update both rows and commit once
        lr.status = models.LeaveStatus.approved
        lr.reviewed_by = user.id
        lr.reviewed_at = datetime.utcnow()
        balance.used_leaves += requested_days
        balance.remaining_leaves = balance.total_leaves - balance.used_leaves

        db.commit()
        db.refresh(lr)
        db.refresh(balance)
    except Exception:
        db.rollback()
        raise

    return {"message":"Leave approved","remaining_leaves": balance.remaining_leaves}

@router.put("/{leave_id}/reject")
def reject_leave(leave_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user.role not in (models.RoleEnum.admin, models.RoleEnum.manager):
        raise HTTPException(status_code=403, detail="Only admin/manager can reject")
    lr = db.query(models.LeaveRequest).filter_by(id=leave_id).first()
    if not lr:
        raise HTTPException(status_code=404, detail="Leave request not found")
    lr.status = models.LeaveStatus.rejected
    lr.reviewed_by = user.id
    lr.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(lr)
    return lr
