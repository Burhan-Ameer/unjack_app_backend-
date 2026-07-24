import pytest
import asyncio
import logging
from sqlalchemy import select
from app.core.db_logging import request_id_ctx, user_id_ctx, AsyncQueueLogHandler, db_log_worker, log_queue
from app.features.logs.models import DBLog

@pytest.mark.asyncio
async def test_db_logging_flow(db_session):
    # 1. Set the mock request and user context
    request_id_ctx.set("test-request-id-123")
    user_id_ctx.set(999)
    
    # 2. Setup logger
    logger = logging.getLogger("app.test_db")
    logger.setLevel(logging.WARNING)
    
    # 3. Emit a warning log
    logger.warning("This is a warning test message")
    
    # 4. Create a mock session factory that returns the active test db_session
    class SessionFactoryMock:
        def __init__(self, session):
            self.session = session
        def __call__(self):
            return self
        async def __aenter__(self):
            return self.session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    # 5. Run the background worker task to process the log record in the queue
    worker_task = asyncio.create_task(db_log_worker(SessionFactoryMock(db_session)))
    
    # Yield control to let the worker task run
    await asyncio.sleep(0.01)
    
    # Wait until the queue is fully drained
    await log_queue.join()

    # Clean up the worker task
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    # 6. Verify that the log is correctly saved in the test database
    result = await db_session.execute(select(DBLog).where(DBLog.request_id == "test-request-id-123"))
    db_log = result.scalar_one_or_none()
    
    assert db_log is not None
    assert db_log.level == "WARNING"
    assert db_log.message == "This is a warning test message"
    assert db_log.user_id == 999
