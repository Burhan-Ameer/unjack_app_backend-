import asyncio
import logging
import traceback
from contextvars import ContextVar
from app.features.logs.models import DBLog

# 1. Thread-safe/Async-safe context variables
request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[int] = ContextVar("user_id", default=None)

# 2. In-memory queue to transition from sync logs to async DB writes
log_queue: asyncio.Queue = asyncio.Queue()


class AsyncQueueLogHandler(logging.Handler):
    """
    Synchronous logging handler that intercepts LogRecords, attaches request_id/user_id
    from context variables, and safely drops them in the in-memory queue.
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Inject request and user context into the record
            record.request_id = request_id_ctx.get()
            record.user_id = user_id_ctx.get()

            # Safely put log record into the queue
            loop = asyncio.get_event_loop()
            if loop.is_running():
                try:
                    log_queue.put_nowait(record)
                except Exception:
                    loop.call_soon_threadsafe(log_queue.put_nowait, record)
        except Exception:
            self.handleError(record)



async def db_log_worker(session_factory) -> None:
    """
    Asynchronous background worker that drains the queue and writes records to PostgreSQL.
    """
    while True:
        try:
            record: logging.LogRecord = await log_queue.get()
            
            try:
                # Format exception traceback if present
                tb_str = None
                if record.exc_info:
                    tb_str = "".join(traceback.format_exception(*record.exc_info))
                    
                # Safely extract context parameters
                req_id = getattr(record, "request_id", None)
                usr_id = getattr(record, "user_id", None)

                # Insert log record into the database asynchronously
                async with session_factory() as session:
                    async with session.begin():
                        db_log = DBLog(
                            level=record.levelname,
                            logger=record.name,
                            message=record.getMessage(),
                            request_id=req_id,
                            user_id=usr_id,
                            traceback=tb_str
                        )
                        session.add(db_log)
            except Exception as e:
                # Fallback printing to console to avoid infinite recursion
                print(f"CRITICAL: Failed to write log to database: {e}", flush=True)
                if 'record' in locals():
                    print(f"Lost Log: {record.levelname} | {record.name} | {record.getMessage()}", flush=True)
            finally:
                log_queue.task_done()
            
        except asyncio.CancelledError:
            break

