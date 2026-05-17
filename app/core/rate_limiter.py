import asyncio
import datetime
import hashlib
import logging
import random
import time

from fastapi import HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.features.auth.models import RateLimitBucket

logger = logging.getLogger(__name__)


class RedisSlidingWindowRateLimiter:
    def __init__(self, redis_url: str, key_prefix: str, max_requests: int, window_seconds: int) -> None:
        self.redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.key_prefix = key_prefix    
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        # --- Circuit Breaker States ---
        self._redis_healthy = True
        self._last_failure_time = 0.0
        self._backoff_cooldown = 5.0  # Start with 5 seconds cooldown
        self._max_backoff = 60.0      # Maximum cooldown is 60 seconds

        # Atomic sliding-window counter limiter.
        # Uses per-window counters (current + previous) and a weighted carryover from the previous window.
        # This avoids storing a per-request log (sorted set) while approximating a true sliding window.
        self._check_lua = """
        local current = redis.call('INCR', KEYS[1])
        redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))

        local prev = tonumber(redis.call('GET', KEYS[2]) or '0')
        local weight = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])

        local total = current + (prev * weight)
        if total > max_requests then    
            redis.call('DECR', KEYS[1])
            return 0
        end
        return 1
        """

    def _resolve_client_key(self, request: Request) -> str:
        # 1. Try forwarded header (only valid in trusted proxy setups like Azure)
        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:
            # take FIRST IP = original client (standard convention in most clouds)
            ip = forwarded_for.split(",")[0].strip()
            if ip:
                return ip

        # 2. Fallback: direct connection IP
        return request.client.host if request.client else "unknown"

    def _redis_key(self, client_key: str) -> str:
        hashed = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:{hashed}"

    def _bucket_key(self, base_key: str, bucket_start: int) -> str:
        return f"{base_key}:{bucket_start}"

    async def _execute_redis_with_retry(self, current_key: str, prev_key: str, ttl_seconds: int, weight: float) -> bool:
        """
        Executes the Redis sliding window script.
        Retries up to 2 times with exponential backoff + jitter if transient errors occur.
        """
        max_retries = 2
        base_delay = 0.02  # Start with 20 milliseconds

        for attempt in range(max_retries + 1):
            try:
                allowed = await self.redis.eval(
                    self._check_lua,
                    2,
                    current_key,
                    prev_key,
                    ttl_seconds,
                    weight,
                    self.max_requests,
                )
                return int(allowed) == 1
            except Exception as exc:
                if attempt == max_retries:
                    # Out of retries, propagate error up to trigger circuit breaker
                    raise exc
                
                # Formula: (base_delay * 2^attempt) + random jitter up to 15ms
                delay = (base_delay * (2 ** attempt)) + random.uniform(0.0, 0.015)
                logger.warning(
                    f"Redis rate limiter transient error on attempt {attempt + 1}. "
                    f"Retrying in {int(delay * 1000)}ms... Error: {exc}"
                )
                await asyncio.sleep(delay)
        return False

    async def _check_postgres_fallback(
        self,
        current_key: str,
        prev_key: str,
        weight: float,
        ttl_seconds: int,
    ) -> bool:
        """
        Saves and increments request counts inside PostgreSQL using an atomic upsert.
        Returns True if request is allowed, False if rate limited.
        """
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=ttl_seconds)
        
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # 1. Atomic Upsert: increment if key exists, otherwise insert with count=1
                stmt = insert(RateLimitBucket).values(
                    key=current_key,
                    count=1,
                    expires_at=expires_at
                )
                upsert_stmt = stmt.on_conflict_do_update(
                    index_elements=[RateLimitBucket.key],
                    set_={RateLimitBucket.count: RateLimitBucket.count + 1}
                ).returning(RateLimitBucket.count)
                
                result = await session.execute(upsert_stmt)
                current_count = result.scalar_one()

                # 2. Get counter from the previous window
                prev_stmt = select(RateLimitBucket.count).where(RateLimitBucket.key == prev_key)
                prev_result = await session.execute(prev_stmt)
                prev_count = prev_result.scalar_one_or_none() or 0

                # 3. Calculate sliding window value
                total = current_count + (prev_count * weight)

                # 4. Enforce limits
                if total > self.max_requests:
                    # Revert count increment to keep data clean
                    decr_stmt = update(RateLimitBucket).where(
                        RateLimitBucket.key == current_key
                    ).values(count=RateLimitBucket.count - 1)
                    await session.execute(decr_stmt)
                    return False

                return True

    async def _get_postgres_count(self, key: str) -> int:
        """
        Helper to fetch a bucket count from Postgres for lazy seeding.
        """
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(RateLimitBucket.count).where(RateLimitBucket.key == key)
                result = await session.execute(stmt)
                return result.scalar_one_or_none() or 0
        except Exception as exc:
            logger.warning(f"Error fetching bucket count from Postgres for lazy seed: {exc}")
            return 0

    async def check(self, request: Request) -> None:
        now = time.time()
        client_key = self._resolve_client_key(request)
        base_key = self._redis_key(client_key)

        bucket_start = int(now // self.window_seconds) * self.window_seconds
        prev_bucket_start = bucket_start - self.window_seconds

        elapsed = now - bucket_start
        weight = (self.window_seconds - elapsed) / self.window_seconds
        ttl_seconds = (self.window_seconds * 2) + 1 

        current_key = self._bucket_key(base_key, bucket_start)
        prev_key = self._bucket_key(base_key, prev_bucket_start)

        is_allowed = False
        redis_success = False

        # Decide whether to check Redis or skip it due to active cooldown
        should_try_redis = self._redis_healthy or (now - self._last_failure_time > self._backoff_cooldown)

        if should_try_redis:
            try:
                # Attempt Redis execution (with quick in-request retries + jitter)
                is_allowed = await self._execute_redis_with_retry(
                    current_key, prev_key, ttl_seconds, weight
                )
                redis_success = True

                # Reset circuit breaker states if recovering
                if not self._redis_healthy:
                    logger.info("Redis server has recovered! Resetting rate limiter to Redis.")
                    self._redis_healthy = True
                    self._backoff_cooldown = 5.0

                # --- Lazy Seeding Recovery ---
                # If we succeeded, check if this is the first request in Redis for this bucket.
                # If yes, synchronize any existing counts accumulated in Postgres while Redis was down.
                if is_allowed:
                    try:
                        redis_count = await self.redis.get(current_key)
                        if redis_count == "1":
                            pg_count = await self._get_postgres_count(current_key)
                            if pg_count > 1:
                                logger.info(f"Lazy seeding Redis bucket {current_key} with Postgres count: {pg_count}")
                                await self.redis.incrby(current_key, pg_count - 1)
                    except Exception as seed_err:
                        logger.warning(f"Error during lazy seeding from Postgres: {seed_err}")

            except Exception as redis_exc:
                # Trip the circuit breaker: Redis is down
                self._redis_healthy = False
                self._last_failure_time = now
                logger.error(
                    f"Redis offline. Tripping circuit breaker. Cooldown set to {self._backoff_cooldown}s. "
                    f"Error: {redis_exc}"
                )
                # Double the backoff cooldown up to max limit
                self._backoff_cooldown = min(self._backoff_cooldown * 2, self._max_backoff)

        # Fallback to PostgreSQL
        if not redis_success:
            try:
                is_allowed = await self._check_postgres_fallback(
                    current_key, prev_key, weight, ttl_seconds
                )
            except Exception as db_exc:
                logger.error(f"Rate Limiter Critical Failure: PostgreSQL fallback failed. Error: {db_exc}")
                raise HTTPException(status_code=503, detail="Rate limiter unavailable")

        if not is_allowed:
            raise HTTPException(status_code=429, detail="Too many requests")
