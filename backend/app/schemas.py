from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

class RoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"

class EmployeeBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    role: RoleEnum = RoleEnum.employee

class EmployeeCreate(EmployeeBase):
    password: str

class EmployeeOut(EmployeeBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: int
    role: Optional[str] = None

class AttendanceCreate(BaseModel):
    employee_id: int

class HolidayCreate(BaseModel):
    name: str
    date: date
    description: Optional[str] = None

class LeaveTypeOut(BaseModel):
    id: int
    name: str
    class Config:
        orm_mode = True

class LeaveRequestCreate(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None

class LeaveRequestOut(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveTypeOut
    start_date: date
    end_date: date
    status: str
    class Config:
        orm_mode = True

class EmployeeListResponse(BaseModel):
    total: int
    items: List['EmployeeOut']  # forward ref

    class Config:
        orm_mode = True

class AttendanceOut(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        orm_mode = True

class AttendanceListResponse(BaseModel):
    total: int
    items: List[AttendanceOut]

    class Config:
        orm_mode = True

# forward refs resolution (if using forward refs for EmployeeOut)
EmployeeListResponse.update_forward_refs()
