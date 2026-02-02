from app.database import SessionLocal, engine, Base
from app.auth import hash_password
from app import models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# create default department
dept = db.query(models.Department).filter_by(name="General").first()
if not dept:
    dept = models.Department(name="General")
    db.add(dept)
    db.commit()
    db.refresh(dept)

# create admin user
admin_email = "admin@example.com"
admin = db.query(models.Employee).filter_by(email=admin_email).first()
if not admin:
    admin = models.Employee(
        first_name="Admin",
        last_name="User",
        email=admin_email,
        password_hash=hash_password("adminpass"),
        role=models.RoleEnum.admin,
        department_id=dept.id
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print("Created admin:", admin.email)
else:
    print("Admin already exists")

# seed leave types
types = ["Sick", "Casual", "Paid", "Unpaid", "Medical"]
for t in types:
    if not db.query(models.LeaveType).filter_by(name=t).first():
        db.add(models.LeaveType(name=t))
db.commit()
print("Seeded leave types")
db.close()
