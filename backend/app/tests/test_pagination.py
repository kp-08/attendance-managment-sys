# app/tests/test_pagination.py
import json
from datetime import date, timedelta

def test_employees_pagination_and_search(client, admin_token, create_employee, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Create 5 employees with distinct names
    emails = []
    for i in range(5):
        em = f"pageuser{i}@example.com"
        create_employee(email=em, password="pass", first=f"Page{i}", last="User")
        emails.append(em)

    # Request page size 2
    r = client.get("/employees/list?skip=0&limit=2", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data and "items" in data
    assert data["total"] >= 5  # total should include seeded admin too
    assert len(data["items"]) == 2

    # Test search by unique first name
    r2 = client.get("/employees/list?q=Page3", headers=headers)
    assert r2.status_code == 200
    data2 = r2.json()
    # expect at least one result and that its name matches
    assert data2["total"] >= 1
    found = False
    for it in data2["items"]:
        if it["first_name"] == "Page3":
            found = True
    assert found

def test_attendance_pagination_and_date_filter(client, admin_token, create_employee, db_session):
    # create employee
    emp = create_employee(email="attpage@example.com", password="pass", first="AttPage", last="User")
    # add 6 attendance rows via db_session for different dates
    import app.models as models
    base_date = date.today()
    for i in range(6):
        ar = models.AttendanceRecord(
            employee_id=emp["id"],
            date=base_date - timedelta(days=i),
            check_in_time=None,
            check_out_time=None,
            status="PRESENT"
        )
        db_session.add(ar)
    db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    # request first page limit 3
    r = client.get(f"/attendance/list?skip=0&limit=3&employee_id={emp['id']}", headers=headers)
    assert r.status_code == 200
    d = r.json()
    assert "total" in d and d["total"] >= 6
    assert len(d["items"]) == 3

    # date filter: only last 2 days
    s_date = (base_date - timedelta(days=1)).isoformat()
    e_date = base_date.isoformat()
    r2 = client.get(f"/attendance/list?start_date={s_date}&end_date={e_date}&employee_id={emp['id']}", headers=headers)
    assert r2.status_code == 200
    d2 = r2.json()
    # Should only return 2 records (base_date and base_date-1)
    assert d2["total"] >= 2
    # check dates in returned items are within range
    for it in d2["items"]:
        assert it["date"] >= s_date and it["date"] <= e_date
