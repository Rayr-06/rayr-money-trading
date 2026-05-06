# RAYR MONEY — Alpaca Integration Backend

Modular Alpaca paper/live trading API. Designed to be added to an existing app
without rewrites.

## Structure
```
backend/
├── services/
│   └── alpaca_client.py        # Alpaca SDK wrapper (stateless)
├── routes/
│   └── alpaca_routes.py        # FastAPI router (POST /connect, /order, etc.)
├── utils/
│   ├── encryption.py           # Fernet symmetric encryption
│   └── credentials_store.py    # Encrypted JSON file store
├── main.py                     # Standalone app entrypoint
├── requirements.txt
└── .gitignore
```

## Setup

```bash
# 1. Install
pip install -r backend/requirements.txt

# 2. (Optional) Set a permanent encryption key. If you skip this, one is
#    generated on first run and persisted to backend/.encryption_key.
export MASTER_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 3. Run the standalone server
uvicorn backend.main:app --reload --port 8000
```

## Environment variables

| Var | Required? | Purpose |
|---|---|---|
| `MASTER_ENCRYPTION_KEY` | optional | Fernet key for encrypting stored credentials. Auto-generated on first run if missing. |
| `ENCRYPTION_KEY_FILE` | optional | Override path for the auto-generated key file. Default: `.encryption_key`. |

That's it. No Alpaca keys go into env — they're submitted via the API.

## API endpoints

| Method | Path | Body | Purpose |
|---|---|---|---|
| POST | `/api/alpaca/connect` | `{api_key, secret_key, paper}` | Validate + store credentials |
| GET | `/api/alpaca/status` | — | Is anything stored? (no secrets returned) |
| GET | `/api/alpaca/test` | — | Validate stored creds + return account snapshot |
| GET | `/api/alpaca/account` | — | Account state (cash, equity, BP) |
| GET | `/api/alpaca/positions` | — | Open positions |
| GET | `/api/alpaca/orders?status_filter=all&limit=50` | — | Order history |
| POST | `/api/alpaca/order` | `{symbol, qty, side, type, time_in_force, limit_price?}` | Place order |
| DELETE | `/api/alpaca/positions/{symbol}` | — | Liquidate position |
| DELETE | `/api/alpaca/disconnect` | — | Forget stored credentials |

## Mounting into an existing FastAPI app

```python
from backend.routes.alpaca_routes import router as alpaca_router
app.include_router(alpaca_router, prefix="/api/alpaca", tags=["alpaca"])
```

## Security notes

- Credentials are encrypted at rest with Fernet (AES-128 + HMAC-SHA256)
- Plaintext keys never leave the backend — frontend only sees masked previews
- File permissions on `.credentials.json` and `.encryption_key` are `0600`
- Validate inputs via Pydantic schemas (length bounds, enums)
- Lock down CORS in `main.py` for production
- Replace the file store with a real DB (Postgres, etc.) for multi-user
