from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Callable, Awaitable
from limiter.ratelimiter import DistributedRateLimiter
from contextlib import asynccontextmanager
from utils.performance import sync_latency
from utils.logger import logger_of
import os

rate_limiter = DistributedRateLimiter(
    brokers=os.getenv('KAFKA_BROKER'), 
    store=os.getenv('REDIS_STORE')
)

logger = logger_of(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rate_limiter.start()
    yield
    await rate_limiter.stop()
    logger.info('CRDT sync latency: %f ms', sync_latency.average() * 1000)

app = FastAPI(lifespan=lifespan)

@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next: Callable[[Request], Awaitable[JSONResponse]]):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return JSONResponse(status_code=400, content={'detail': 'Missing X-User-Id header'})
    allowed, node_id = rate_limiter.allow_request(user_id)
    if not allowed:
        return JSONResponse(status_code=429, content={'detail': 'Too Many Requests'})
    response = await call_next(request)
    response.headers['X-Limiter-Node'] = node_id
    return response

@app.get('/protected')
async def protected() -> dict[str, str]:
    return {'message': 'You accessed a protected route!'}