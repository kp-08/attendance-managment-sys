# app/tests/test_employees.py
import json

def test_create_employee_as_admin(client, admin_token):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "password": "testpass",
        "phone": "9999999999",
        "designation": "Intern",
        "department_id": 1,
        "role": "employee"
    }
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post("/employees/create", headers=headers, json=payload)
    assert resp.status_code == 200 or resp.status_code == 201
    data = resp.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_list_employees(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/employees/list", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1