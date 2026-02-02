from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
from app.auth import hash_password
from app.deps import get_current_user

from sqlalchemy import or_

router = APIRouter(prefix="/employees", tags=["employees"])

@router.post("/create", response_model=schemas.EmployeeOut)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    # only admin can create
    if user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only admin can create employees")
    existing = db.query(models.Employee).filter(models.Employee.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(payload.password)
    emp = models.Employee(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password_hash=hashed,
        phone=payload.phone,
        designation=payload.designation,
        department_id=payload.department_id,
        role=payload.role
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

@router.get("/list", response_model=schemas.EmployeeListResponse)
def list_employees(
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    Paginated list of employees with optional free-text search and sorting.

    Params:
    - skip, limit : pagination
    - q : free-text search across first_name,last_name,email,phone,designation
    - sort_by : one of allowed fields (first_name,last_name,email,designation,created_at)
    - order : 'asc' or 'desc'
    """
    allowed_sort_fields = {"first_name", "last_name", "email", "designation", "created_at"}

    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")

    query = db.query(models.Employee)

    # access control
    if user.role == models.RoleEnum.employee:
        query = query.filter(models.Employee.id == user.id)

    # search
    if q:
        q_like = f"%{q}%"
        query = query.filter(
            or_(
                models.Employee.first_name.ilike(q_like),
                models.Employee.last_name.ilike(q_like),
                models.Employee.email.ilike(q_like),
                models.Employee.phone.ilike(q_like),
                models.Employee.designation.ilike(q_like),
            )
        )

    # sorting
    if sort_by:
        if sort_by not in allowed_sort_fields:
            raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Allowed: {sorted(list(allowed_sort_fields))}")
        col = getattr(models.Employee, sort_by)
        if order == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": items}

@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    emp = db.query(models.Employee).filter(models.Employee.id==employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp
