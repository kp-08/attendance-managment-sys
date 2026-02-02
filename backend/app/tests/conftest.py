# app/tests/conftest.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app import models
from app.auth import hash_password

@pytest.fixture(scope="session")
def client():
    """
    Start with a clean DB schema for the test session.
    WARNING: This will DROP and CREATE all tables in the configured DATABASE_URL.
    """
    # Create all tables (fresh)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed minimal lookup data: a department and some leave types
    db = SessionLocal()
    dept = models.Department(name="General")
    db.add(dept)
    db.commit()
    db.refresh(dept)

    # seed leave types
    for name in ["Sick", "Casual", "Paid", "Unpaid"]:
        if not db.query(models.LeaveType).filter_by(name=name).first():
            db.add(models.LeaveType(name=name))
    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c

    # Teardown after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Provide a fresh DB session for tests that need direct DB access.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def admin_token(client, db_session):
    """
    Create an admin user directly in DB and return a JWT token via the login endpoint.
    """
    # create admin (if not exists)
    admin_email = "admin@example.com"
    admin = db_session.query(models.Employee).filter_by(email=admin_email).first()
    if not admin:
        dept = db_session.query(models.Department).filter_by(name="General").first()
        admin = models.Employee(
            first_name="Admin",
            last_name="User",
            email=admin_email,
            password_hash=hash_password("adminpass"),
            role=models.RoleEnum.admin,
            department_id=dept.id
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

    # login via API to get token
    resp = client.post("/auth/login", data={"username": admin_email, "password": "adminpass"})
    assert resp.status_code == 200, "Admin login failed during fixture setup"
    token = resp.json()["access_token"]
    return token

@pytest.fixture
def create_employee(db_session):
    """
    Helper to create an employee in DB directly for tests.
    Returns a function to call when needed.
    """
    def _create(email="emp1@example.com", password="emppass", first="Emp", last="One"):
        dept = db_session.query(models.Department).filter_by(name="General").first()
        emp = models.Employee(
            first_name=first,
            last_name=last,
            email=email,
            password_hash=hash_password(password),
            role=models.RoleEnum.employee,
            department_id=dept.id
        )
        db_session.add(emp)
        db_session.commit()
        db_session.refresh(emp)
        return {"id": emp.id, "email": emp.email, "password": password}
    return _create
