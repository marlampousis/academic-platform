from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.users.router import router as users_router
from app.auth.router import router as auth_router

from app.institutions.router import router as institutions_router
from app.departments.router import router as departments_router
from app.profiles.router import router as profiles_router
from app.degrees.router import router as degrees_router
from app.publications.router import router as publications_router
from app.research_projects.router import router as research_projects_router
from app.teaching_experience.router import router as teaching_experience_router

from app.openalex.router import router as openalex_router
from app.metrics.router import router as metrics_router
from app.summaries.router import router as summaries_router

from app.orcid.router import router as orcid_router

app = FastAPI(
    title="Academic Platform API",
    version="0.1.0"
)

app.include_router(users_router)
app.include_router(auth_router)

app.include_router(institutions_router)
app.include_router(departments_router)

app.include_router(profiles_router)
app.include_router(degrees_router)
app.include_router(publications_router)
app.include_router(research_projects_router)
app.include_router(teaching_experience_router)

app.include_router(openalex_router)
app.include_router(metrics_router)
app.include_router(summaries_router)

app.include_router(orcid_router)

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