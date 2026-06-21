from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.users.router import router as users_router
from app.auth.router import router as auth_router

from app.institutions.router import router as institutions_router
from app.departments.router import router as departments_router
from app.profiles.router import router as profiles_router

app = FastAPI(
    title="Academic Platform API",
    version="0.1.0"
)

app.include_router(users_router)
app.include_router(auth_router)

app.include_router(institutions_router)
app.include_router(departments_router)

app.include_router(profiles_router)

@app.get("/")
def root():
    return {"message": "Academic Platform API is running"}


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database_connected": True,
        "result": value
    }
    
from app.core.config import settings


@app.get("/debug-db-url")
def debug_db_url():
    return {
        "database_url": settings.DATABASE_URL
    }    