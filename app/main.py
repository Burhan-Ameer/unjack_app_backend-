import asyncio
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.error_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.api.v1.router import api_router
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
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    
    # Store request id in task-local context variable
    from app.core.db_logging import request_id_ctx
    request_id_ctx.set(request_id)
    
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

from app.db.session import engine, Base  # noqa: E402
from app.features.scheduler import scheduler, setup_scheduler  # noqa: E402
from app.dependencies import redis_client  # noqa: E402


db_logging_task = None


@app.on_event("startup")
async def startup_event() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start the non-blocking background logger task
    global db_logging_task
    from app.core.db_logging import db_log_worker
    from app.db.session import AsyncSessionLocal
    db_logging_task = asyncio.create_task(db_log_worker(AsyncSessionLocal))
    
    setup_scheduler()
    scheduler.start()
    logger.info("FastAPI: Background scheduler started.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    # Safely cancel the logging worker task
    if db_logging_task:
        db_logging_task.cancel()
        try:
            await db_logging_task
        except asyncio.CancelledError:
            pass
            
    scheduler.shutdown()
    await redis_client.close()
    logger.info("FastAPI: Background scheduler and Redis connections shut down.")

