import hashlib
import time
from urllib import request

from fastapi import HTTPException, Request
from redis.asyncio import Redis


class RedisSlidingWindowRateLimiter:
    def __init__(self, redis_url: str, key_prefix: str, max_requests: int, window_seconds: int) -> None:
        self.redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.key_prefix = key_prefix    
        self.max_requests = max_requests
        self.window_seconds = window_seconds

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

    async def check(self, request: Request) -> None:
        now = time.time()
        client_key = self._resolve_client_key(request)
        base_key = self._redis_key(client_key)

        bucket_start = int(now // self.window_seconds) * self.window_seconds
        prev_bucket_start = bucket_start - self.window_seconds

        elapsed = now - bucket_start
        # Weight of the previous window that still overlaps the current sliding window.
        weight = (self.window_seconds - elapsed) / self.window_seconds
        ttl_seconds = (self.window_seconds * 2) + 1 

        current_key = self._bucket_key(base_key, bucket_start)
        prev_key = self._bucket_key(base_key, prev_bucket_start)

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
        except Exception:
            raise HTTPException(status_code=503, detail="Rate limiter unavailable")

        if int(allowed) != 1:
            raise HTTPException(status_code=429, detail="Too many requests")
