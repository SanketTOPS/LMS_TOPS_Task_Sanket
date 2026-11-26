from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.error_handler import register_exception_handlers
from app.routers import (
    assignments,
    attendance,
    auth,
    batches,
    certificates,
    courses,
    instructors,
    lectures,
    materials,
    payments,
    progress,
    quizzes,
    students,
    users,
)
from app.utils.limiter import limiter

show_docs = settings.DEBUG or settings.ENABLE_API_DOCS or settings.APP_ENV != "production"

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/api/docs" if show_docs else None,
    redoc_url="/api/redoc" if show_docs else None,
    openapi_url="/api/openapi.json" if show_docs else None,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(batches.router)
app.include_router(students.router)
app.include_router(instructors.router)
app.include_router(lectures.router)
app.include_router(materials.router)
app.include_router(assignments.router)
app.include_router(quizzes.router)
app.include_router(attendance.router)
app.include_router(progress.router)
app.include_router(payments.router)
app.include_router(certificates.router)


@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> JSONResponse:
    """Health check endpoint verifying API liveness and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "database": "connected",
                "app": settings.APP_NAME,
                "env": settings.APP_ENV,
            },
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "database": "disconnected",
                "app": settings.APP_NAME,
                "env": settings.APP_ENV,
            },
        )
