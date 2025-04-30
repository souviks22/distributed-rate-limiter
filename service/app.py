import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from limiter.kafka_sync import KafkaSync
from limiter.limiter import DistributedRateLimiter

kafka_sync = KafkaSync(os.getenv('KAFKA_BROKER'), topic='rate-limiter', capacity=10, refill_rate=1.0)
rate_limiter = DistributedRateLimiter(kafka_sync)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rate_limiter.start()
    yield
    await rate_limiter.stop()

app = FastAPI(lifespan=lifespan)

@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next):
    user_id: str = request.headers.get('X-User-Id')
    if not user_id:
        return JSONResponse(status_code=400, content={'detail': 'Missing X-User-Id header'})
    
    allowed: bool = await rate_limiter.allow_request(user_id)
    if not allowed:
        return JSONResponse(status_code=429, content={'detail': 'Too Many Requests'})
    
    return await call_next(request)

@app.get('/protected')
async def protected() -> dict[str, str]:
    return {'message': 'You accessed a protected route!'}