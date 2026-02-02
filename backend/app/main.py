from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, employees, attendance, holidays, leaves
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Attendance + Phonebook API")

# create tables (for development only; prefer alembic migrations)
#Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(holidays.router)
app.include_router(leaves.router)



origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

