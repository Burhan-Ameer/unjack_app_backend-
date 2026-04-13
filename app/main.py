import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.error_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from fastapi.security import OAuth2PasswordBearer
setup_logging()
logger = logging.getLogger("app")

app = FastAPI(title="Unjack Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    start = time.perf_counter()
    logger.info("Request started id=%s method=%s path=%s", request_id, request.method, request.url.path)

    response = await call_next(request)

    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["x-request-id"] = request_id
    logger.info(
        "Request finished id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


register_exception_handlers(app)

app.include_router(api_router, prefix="/api/v1")

# Initialize database tables on startup for environments without Alembic migrations.
from app.db.session import engine, Base  # noqa: E402


@app.on_event("startup")
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
