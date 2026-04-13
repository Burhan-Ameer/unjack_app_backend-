import hashlib
import time
from uuid import uuid4

from fastapi import HTTPException, Request
from redis.asyncio import Redis


class RedisSlidingWindowRateLimiter:
    def __init__(self, redis_url: str, key_prefix: str, max_requests: int, window_seconds: int) -> None:
        self.redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.key_prefix = key_prefix    
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def _resolve_client_key(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", maxsplit=1)[0].strip()
        return request.client.host if request.client else "unknown"

    def _redis_key(self, client_key: str) -> str:
        hashed = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:{hashed}"

    async def check(self, request: Request) -> None:
        now = time.time()
        client_key = self._resolve_client_key(request)
        redis_key = self._redis_key(client_key)
        window_start = now - self.window_seconds
        member = f"{now}:{uuid4().hex}"

        try:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(redis_key, 0, window_start)
                pipe.zadd(redis_key, {member: now})
                pipe.zcard(redis_key)
                pipe.expire(redis_key, self.window_seconds + 1)
                result = await pipe.execute()
        except Exception:
            raise HTTPException(status_code=503, detail="Rate limiter unavailable")

        request_count = int(result[2])
        if request_count > self.max_requests:
            await self.redis.zrem(redis_key, member)
            raise HTTPException(status_code=429, detail="Too many requests")
