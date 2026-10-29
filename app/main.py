import asyncio
import logging
import os
import time

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("monitoring-demo")

API_KEY = os.getenv("API_KEY", "secret123")

app = FastAPI(title="API Monitoring Demo", version="1.0.0")

USERS = [
    {"id": 1, "name": "Rohan", "email": "rohan@example.com"},
    {"id": 2, "name": "Ashish", "email": "ashish@example.com"},
    {"id": 3, "name": "Karan", "email": "karan@example.com"},
]
PRODUCTS = [
    {"id": 101, "name": "Laptop", "price": 85000},
    {"id": 102, "name": "Headphones", "price": 1500},
    {"id": 103, "name": "Keyboard", "price": 1200},
]


# Inner middleware: catches crashes, logs the traceback (root cause info)
# and returns a clean 500 so the metrics layer can count it.
@app.middleware("http")
async def catch_errors(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("UNHANDLED ERROR on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "exception": type(exc).__name__,
                "detail": str(exc),
                "path": request.url.path,
            },
        )
    elapsed = time.perf_counter() - start
    if request.url.path != "/metrics":
        logger.info("%s %s -> %s (%.3fs)", request.method, request.url.path,
                    response.status_code, elapsed)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/users")
def users():
    return USERS


@app.get("/products")
def products():
    return PRODUCTS


@app.get("/protected")
def protected(x_api_key: str | None = Header(default=None)):
    """Used for Scenario 1: invalid API authentication."""
    if x_api_key != API_KEY:
        logger.warning("AUTH FAILURE: invalid or missing X-API-Key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return {"message": "You are authenticated"}


@app.get("/simulate-error")
def simulate_error():
    raise RuntimeError("Simulated database connection failure")


@app.get("/simulate-timeout")
async def simulate_timeout(delay: int = 5):
    await asyncio.sleep(delay)
    return {"message": f"Responded after {delay} seconds"}


@app.get("/simulate-rate-limit")
def simulate_rate_limit():
    logger.warning("RATE LIMIT exceeded")
    return JSONResponse(
        status_code=429,
        content={"error": "Too Many Requests", "detail": "Rate limit exceeded"},
        headers={"Retry-After": "60"},
    )


# Outer middleware: Prometheus metrics at /metrics (must be added AFTER catch_errors)
Instrumentator(
    should_group_status_codes=False,   # keep exact codes: 200, 401, 429, 500
    excluded_handlers=["/metrics"],
).instrument(app).expose(app)
