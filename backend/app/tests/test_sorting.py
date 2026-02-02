# app/tests/test_sorting.py
from datetime import date, timedelta

def test_employees_sorting(client, admin_token, create_employee):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # create employees with known first_names to check sorting
    create_employee(email="sorta@example.com", password="p", first="Alpha", last="A")
    create_employee(email="sortb@example.com", password="p", first="Charlie", last="C")
    create_employee(email="sortc@example.com", password="p", first="Bravo", last="B")

    # sort by first_name ascending
    r = client.get("/employees/list?sort_by=first_name&order=asc", headers=headers)
    assert r.status_code == 200
    data = r.json()
    names = [item["first_name"] for item in data["items"]]
    # the returned page may have other seeded users; just assert the sequence for the created names is sorted among items containing them
    # Ensure that Alpha, Bravo, Charlie appear in that order in the items list (they may not be contiguous but order preserved)
    alpha_idx = next((i for i, v in enumerate(names) if v == "Alpha"), None)
    bravo_idx = next((i for i, v in enumerate(names) if v == "Bravo"), None)
    charlie_idx = next((i for i, v in enumerate(names) if v == "Charlie"), None)
    assert alpha_idx is not None and bravo_idx is not None and charlie_idx is not None
    assert alpha_idx < bravo_idx < charlie_idx

    # sort by first_name descending
    r2 = client.get("/employees/list?sort_by=first_name&order=desc", headers=headers)
    assert r2.status_code == 200
    data2 = r2.json()
    names2 = [item["first_name"] for item in data2["items"]]
    alpha_idx2 = next((i for i, v in enumerate(names2) if v == "Alpha"), None)
    bravo_idx2 = next((i for i, v in enumerate(names2) if v == "Bravo"), None)
    charlie_idx2 = next((i for i, v in enumerate(names2) if v == "Charlie"), None)
    assert charlie_idx2 < bravo_idx2 < alpha_idx2

def test_attendance_sorting(client, admin_token, create_employee, db_session):
    # create employee
    emp = create_employee(email="sortatt@example.com", password="p", first="SortAtt", last="User")
    # insert attendance rows with different dates
    import app.models as models
    base = date.today()
    # create dates: base-2, base-1, base
    dates = [base - timedelta(days=2), base - timedelta(days=1), base]
    for d in dates:
        ar = models.AttendanceRecord(employee_id=emp["id"], date=d, status="PRESENT")
        db_session.add(ar)
    db_session.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    # ascending by date
    r = client.get(f"/attendance/list?employee_id={emp['id']}&sort_by=date&order=asc", headers=headers)
    assert r.status_code == 200
    d = r.json()
    returned_dates = [item["date"] for item in d["items"]]
    # dates should be in ascending iso strings
    assert returned_dates == sorted(returned_dates)

    # descending by date
    r2 = client.get(f"/attendance/list?employee_id={emp['id']}&sort_by=date&order=desc", headers=headers)
    assert r2.status_code == 200
    d2 = r2.json()
    returned_dates2 = [item["date"] for item in d2["items"]]
    assert returned_dates2 == sorted(returned_dates2, reverse=True)
