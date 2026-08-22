"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import broadcast, geofence, location, safety_resource, ai, identity
from app.config.settings import settings
from app.database.connection import SessionLocal, init_db
from app.schemas.common import ErrorResponse
from app.seed import run_seed
from app.utils.exceptions import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if not settings.debug or settings.database_url.startswith("sqlite"):
        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Location tracking and geofencing backend for SIH Tourist Safety System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.message).model_dump(),
    )


app.include_router(location.router, prefix="/api/v1")
app.include_router(geofence.router, prefix="/api/v1")
app.include_router(safety_resource.router, prefix="/api/v1")
app.include_router(broadcast.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(identity.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "location-geofencing"}


@app.get("/api/v1/test-coordinates", tags=["testing"])
def get_test_coordinates() -> dict[str, object]:
    from app.seed import TEST_COORDINATES

    formatted = {
        key: {"latitude": lat, "longitude": lng}
        for key, (lat, lng) in TEST_COORDINATES.items()
    }
    return {"success": True, "data": formatted}
