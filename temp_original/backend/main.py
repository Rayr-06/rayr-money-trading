"""
Standalone FastAPI app for the Alpaca integration.

Run:
    uvicorn backend.main:app --reload --port 8000

Or mount the router into your existing trading_system.api:app — see
the bottom of this file for the snippet.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.alpaca_routes import router as alpaca_router


app = FastAPI(title="RAYR MONEY — Alpaca API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(alpaca_router, prefix="/api/alpaca", tags=["alpaca"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "alpaca-integration"}


# ─────────────────────────────────────────────────────────────────────────────
# To mount on your EXISTING trading_system.api app, add this to api.py:
#
#   from backend.routes.alpaca_routes import router as alpaca_router
#   app.include_router(alpaca_router, prefix="/api/alpaca", tags=["alpaca"])
#
# ─────────────────────────────────────────────────────────────────────────────
