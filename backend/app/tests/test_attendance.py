# app/tests/test_attendance.py
import pytest

def get_token_for(client, email, password):
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_check_in_and_out(client, create_employee):
    # create an employee in DB
    emp = create_employee(email="attn@example.com", password="attnpass", first="Attn", last="User")
    token = get_token_for(client, emp["email"], emp["password"])
    headers = {"Authorization": f"Bearer {token}"}

    # check-in
    r1 = client.post("/attendance/check-in", headers=headers)
    assert r1.status_code == 200
    j1 = r1.json()
    assert j1.get("employee_id") == emp["id"] or j1.get("employee_id") == emp["id"]

    # double check-in should fail
    r_double = client.post("/attendance/check-in", headers=headers)
    assert r_double.status_code == 400

    # check-out
    r2 = client.post("/attendance/check-out", headers=headers)
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2.get("check_out_time") is not None
