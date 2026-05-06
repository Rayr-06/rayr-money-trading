/**
 * Alpaca API client (frontend → backend).
 * Plain fetch — no extra deps. Returns parsed JSON or throws an ApiError.
 */

const DEFAULT_BASE =
  (typeof window !== "undefined" && (window as any).__API_BASE__) ||
  (import.meta as any).env?.VITE_API_BASE ||
  "http://localhost:8000";

export const API_BASE = DEFAULT_BASE.replace(/\/$/, "");

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init.headers || {}),
      },
    });
  } catch (e: any) {
    throw new ApiError(
      `Cannot reach backend at ${API_BASE}. Is uvicorn running?`,
      "network_error",
      0,
    );
  }
  let body: any = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON response */
  }
  if (!res.ok) {
    const detail = body?.detail || body || {};
    const msg =
      typeof detail === "string"
        ? detail
        : detail.message || res.statusText || "Request failed";
    const code = (typeof detail === "object" && detail.code) || "http_error";
    throw new ApiError(msg, code, res.status);
  }
  return body as T;
}

// ─── Types ────────────────────────────────────────────────────────────

export interface AlpacaAccount {
  account_number: string;
  status: string;
  currency: string;
  cash: number;
  equity: number;
  buying_power: number;
  portfolio_value: number;
  pattern_day_trader: boolean;
  trading_blocked: boolean;
  account_blocked: boolean;
  is_paper: boolean;
}

export interface AlpacaPosition {
  symbol: string;
  qty: number;
  side: string;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
}

export interface AlpacaOrder {
  id: string;
  symbol: string;
  qty: number;
  filled_qty: number;
  side: string;
  status: string;
  submitted_at: string;
  filled_avg_price: number;
}

export interface ConnectionStatus {
  connected: boolean;
  mode?: "paper" | "live";
  api_key_masked?: string;
}

// ─── Endpoints ────────────────────────────────────────────────────────

export const alpacaApi = {
  status: () => request<ConnectionStatus>("/api/alpaca/status"),

  connect: (api_key: string, secret_key: string, paper: boolean) =>
    request<{
      ok: boolean;
      message: string;
      mode: "paper" | "live";
      account: Partial<AlpacaAccount>;
    }>("/api/alpaca/connect", {
      method: "POST",
      body: JSON.stringify({ api_key, secret_key, paper }),
    }),

  test: () =>
    request<{ ok: boolean; account: AlpacaAccount; clock: any }>(
      "/api/alpaca/test",
    ),

  account: () => request<AlpacaAccount>("/api/alpaca/account"),

  positions: () =>
    request<{ positions: AlpacaPosition[] }>("/api/alpaca/positions"),

  orders: (status_filter = "all", limit = 50) =>
    request<{ orders: AlpacaOrder[] }>(
      `/api/alpaca/orders?status_filter=${status_filter}&limit=${limit}`,
    ),

  placeOrder: (
    symbol: string,
    qty: number,
    side: "buy" | "sell",
    type: "market" | "limit" = "market",
    time_in_force: "day" | "gtc" | "ioc" | "fok" = "day",
    limit_price?: number,
  ) =>
    request<AlpacaOrder>("/api/alpaca/order", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        qty,
        side,
        type,
        time_in_force,
        limit_price,
      }),
    }),

  closePosition: (symbol: string) =>
    request<{ closed: string }>(`/api/alpaca/positions/${symbol}`, {
      method: "DELETE",
    }),

  disconnect: () =>
    request<{ deleted: boolean }>("/api/alpaca/disconnect", {
      method: "DELETE",
    }),
};
