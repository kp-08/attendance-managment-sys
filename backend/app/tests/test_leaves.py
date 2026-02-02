# app/tests/test_leaves.py
from datetime import date, timedelta

def get_token_for(client, email, password):
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_apply_and_approve_leave(client, create_employee, admin_token):
    # create an employee
    emp = create_employee(email="leaveuser@example.com", password="leavepass", first="Leave", last="User")
    user_token = get_token_for(client, emp["email"], emp["password"])
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # pick a leave type id (we seeded 1..n in conftest)
    # apply leave for 2 days
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post("/leave/apply", headers=user_headers, json={
        "leave_type_id": 1,
        "start_date": start,
        "end_date": end,
        "reason": "Test leave"
    })
    assert resp.status_code == 200
    lr = resp.json()
    leave_id = lr["id"]

    # approve as admin
    r2 = client.put(f"/leave/{leave_id}/approve", headers=admin_headers)
    assert r2.status_code == 200
    j2 = r2.json()
    assert "remaining_leaves" in j2
    assert j2["message"] == "Leave approved"
