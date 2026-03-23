import time
import logging
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.database import init_db
from app.core.config import settings
from app.api import auth, documents, chat, vin, compare, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="Car Contract AI", version="1.0.0")
logger = logging.getLogger("app.startup")
request_logger = logging.getLogger("app.request")
error_logger = logging.getLogger("app.error")

frontend_origins = [
    origin.strip().rstrip("/")
    for origin in settings.FRONTEND_URL.split(",")
    if origin.strip()
]
frontend_origin = frontend_origins[0] if frontend_origins else ""
additional_origins = [
    origin.strip().rstrip("/")
    for origin in settings.CORS_ADDITIONAL_ORIGINS.split(",")
    if origin.strip()
]
cors_origins = list(filter(None, {
    *frontend_origins,
    *additional_origins,
    "http://localhost:5173",
    "http://localhost:3000",
}))

async def recover_stuck_documents():
    """
    On startup: find ALL documents stuck in 'processing' or
    'extraction_complete'. Reset them to 'sla_failed' so the
    retry button appears.
    Any background tasks from a previous server process are dead,
    so there's no risk of racing with an active task.
    Runs in background without blocking startup.
    """
    from sqlalchemy import update as sql_update
    from app.models.models import Document
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                sql_update(Document)
                .where(
                    Document.processing_status.in_(
                        ["processing", "extraction_complete"]
                    ),
                )
                .values(
                    processing_status="sla_failed",
                    error_message=(
                        "Analysis was interrupted. "
                        "Click Retry to try again."
                    ),
                )
            )
            await db.commit()
            count = result.rowcount
            if count > 0:
                logger.info(
                    "[startup] Recovered %d stuck document(s)",
                    count
                )
        except Exception:
            logger.exception("[startup] Stuck document recovery failed")


@app.on_event("startup")
async def startup():
    init_db(settings.DATABASE_URL)
    logger.info(
        "startup config: frontend_url_raw=%s frontend_url_normalized=%s cors_additional_origins=%s cors_allow_origin_regex=%s app_base_url=%s cookie_secure=%s cookie_samesite=%s",
        settings.FRONTEND_URL,
        frontend_origins,
        additional_origins,
        settings.CORS_ALLOW_ORIGIN_REGEX,
        settings.APP_BASE_URL,
        settings.COOKIE_SECURE,
        settings.COOKIE_SAMESITE,
    )
    if settings.COOKIE_SAMESITE.lower() == "none" and not settings.COOKIE_SECURE:
        logger.warning(
            "cookie config warning: COOKIE_SAMESITE=none with COOKIE_SECURE=false; browsers will reject refresh cookie over HTTPS"
        )
    # Run document recovery in background without blocking startup
    asyncio.create_task(recover_stuck_documents())


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        request_logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        error_logger.exception(
            "unhandled request error: %s %s (%.1f ms)",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_logger.warning(
        "http error: %s %s -> %s detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_logger.warning(
        "validation error: %s %s errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_logger.exception(
        "unhandled exception: %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"] is incompatible with allow_credentials=True.
    # List every frontend origin explicitly.
    allow_origins=cors_origins,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX or None,
    allow_credentials=True,             # needed for HTTP-only cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(vin.router, prefix="/vin", tags=["VIN"])
app.include_router(compare.router, prefix="/compare", tags=["Compare"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {"status": "running", "docs": "/docs"}