from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from application.routers import (
    auth_router,
    users_router,
    traders_router,
    admin_router,
    subscriptions_router,
    keys_router,
    wallet_router,
    webhooks_router,
    waitlist_router,
    virtual_wallet_router,
    payments_router
)
from application.utilities import exceptions as es
from application.utilities.audit import setup_logger
from application.utilities.rate_limit import limiter, rate_limit_exceeded_handler

logger = setup_logger(__name__)

app = FastAPI(
    title="JARS API",
    version="1.0.0",
    description="CEX-CT API"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(es.JARSException)
async def jars_exception_handler(request: Request, exc: es.JARSException):
    status_code = es.get_http_status_for_exception(exc)
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.code, "message": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
    )


@app.get("/health")
async def health_check():
    return {"status": "We up!", "service": "JARS API"}


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(traders_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(keys_router, prefix="/api/v1")
app.include_router(wallet_router, prefix="/api/v1")
app.include_router(virtual_wallet_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(waitlist_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
