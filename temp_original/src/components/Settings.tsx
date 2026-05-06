/**
 * Alpaca connection Settings panel.
 *
 * Drop into your app:
 *   import Settings from './components/Settings';
 *   <Settings />
 *
 * Talks to backend routes from backend/routes/alpaca_routes.py.
 * Override API base URL via `VITE_API_BASE` env var.
 */
import { useEffect, useState } from "react";
import {
  alpacaApi,
  ApiError,
  API_BASE,
  type AlpacaAccount,
  type ConnectionStatus,
} from "../services/api";

type Toast = { kind: "ok" | "err"; msg: string } | null;

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [paper, setPaper] = useState(true);
  const [showSecret, setShowSecret] = useState(false);

  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [account, setAccount] = useState<AlpacaAccount | null>(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [toast, setToast] = useState<Toast>(null);
  const [backendUp, setBackendUp] = useState<boolean | null>(null);

  // Initial status check
  useEffect(() => {
    void refreshStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function flash(t: Toast, ms = 4000) {
    setToast(t);
    if (t) setTimeout(() => setToast(null), ms);
  }

  async function refreshStatus() {
    try {
      const s = await alpacaApi.status();
      setStatus(s);
      setBackendUp(true);
      if (s.connected) {
        setPaper(s.mode === "paper");
        try {
          const a = await alpacaApi.account();
          setAccount(a);
        } catch {
          /* connected flag true but account fetch failed — keep going */
        }
      } else {
        setAccount(null);
      }
    } catch (e: any) {
      setBackendUp(false);
    }
  }

  async function handleSave() {
    if (!apiKey.trim() || !secretKey.trim()) {
      flash({ kind: "err", msg: "Both API key and secret are required." });
      return;
    }
    setLoading(true);
    try {
      const r = await alpacaApi.connect(apiKey.trim(), secretKey.trim(), paper);
      flash({
        kind: "ok",
        msg: `Connected ✓  Mode: ${r.mode.toUpperCase()}  Acct: ${r.account.account_number}`,
      });
      // Don't keep the typed secret in component state after success
      setApiKey("");
      setSecretKey("");
      setShowSecret(false);
      await refreshStatus();
    } catch (e: any) {
      flash({
        kind: "err",
        msg:
          e instanceof ApiError
            ? `${e.message} [${e.code}]`
            : e?.message || "Save failed",
      });
    } finally {
      setLoading(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    try {
      const r = await alpacaApi.test();
      setAccount(r.account);
      flash({
        kind: "ok",
        msg: `Test passed ✓  Cash: $${r.account.cash.toLocaleString()}  Market ${r.clock.is_open ? "OPEN" : "closed"}`,
      });
    } catch (e: any) {
      flash({
        kind: "err",
        msg:
          e instanceof ApiError
            ? `${e.message} [${e.code}]`
            : e?.message || "Test failed",
      });
    } finally {
      setTesting(false);
    }
  }

  async function handleDisconnect() {
    if (
      !confirm(
        "Forget the stored Alpaca credentials? You'll need to re-enter them to trade.",
      )
    )
      return;
    try {
      await alpacaApi.disconnect();
      setAccount(null);
      flash({ kind: "ok", msg: "Disconnected." });
      await refreshStatus();
    } catch (e: any) {
      flash({ kind: "err", msg: e?.message || "Disconnect failed" });
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900/60 to-zinc-950 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-zinc-100">
              ⚙️ Alpaca Connection
            </h2>
            <p className="mt-1 text-sm text-zinc-400">
              Enter your Alpaca API credentials. They're sent to the backend
              over HTTPS, encrypted at rest with Fernet, and never stored in
              the browser.
            </p>
          </div>
          <BackendBadge up={backendUp} />
        </div>
      </div>

      {/* Backend down warning */}
      {backendUp === false && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-4 text-sm">
          <p className="font-semibold text-rose-300">
            ✗ Cannot reach backend at{" "}
            <code className="font-mono">{API_BASE}</code>
          </p>
          <p className="mt-2 text-zinc-300">Start the backend:</p>
          <pre className="mt-2 overflow-x-auto rounded bg-zinc-950 p-3 font-mono text-xs text-emerald-300">
            uvicorn backend.main:app --reload --port 8000
          </pre>
        </div>
      )}

      {/* Status card */}
      <ConnectionCard
        status={status}
        account={account}
        onTest={handleTest}
        onDisconnect={handleDisconnect}
        testing={testing}
      />

      {/* Form */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-zinc-300">
          {status?.connected ? "Update credentials" : "Connect Alpaca"}
        </h3>

        <div className="space-y-4">
          {/* API Key */}
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              API Key
            </label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="PK..."
              autoComplete="off"
              spellCheck={false}
              className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-100 placeholder-zinc-600 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          {/* Secret Key */}
          <div>
            <label className="mb-1 flex items-center justify-between text-xs font-medium text-zinc-400">
              <span>Secret Key</span>
              <button
                type="button"
                onClick={() => setShowSecret(!showSecret)}
                className="text-[11px] text-emerald-400 hover:text-emerald-300"
              >
                {showSecret ? "hide" : "show"}
              </button>
            </label>
            <input
              type={showSecret ? "text" : "password"}
              value={secretKey}
              onChange={(e) => setSecretKey(e.target.value)}
              placeholder="••••••••••••••••••••••••••••••••"
              autoComplete="off"
              spellCheck={false}
              className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-sm text-zinc-100 placeholder-zinc-600 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          {/* Mode toggle */}
          <div>
            <label className="mb-2 block text-xs font-medium text-zinc-400">
              Trading Mode
            </label>
            <div className="inline-flex rounded-md border border-zinc-700 p-1">
              <button
                type="button"
                onClick={() => setPaper(true)}
                className={`rounded px-4 py-1.5 text-sm font-semibold transition ${
                  paper
                    ? "bg-emerald-500 text-zinc-950"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                📝 PAPER
              </button>
              <button
                type="button"
                onClick={() => setPaper(false)}
                className={`rounded px-4 py-1.5 text-sm font-semibold transition ${
                  !paper
                    ? "bg-rose-500 text-zinc-950"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                💰 LIVE
              </button>
            </div>
            {!paper && (
              <p className="mt-2 text-xs text-rose-300">
                ⚠ LIVE mode places orders with real money. Are you sure?
              </p>
            )}
          </div>

          {/* Save button */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={loading || backendUp === false}
              className="rounded-md bg-emerald-500 px-5 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Validating..." : "Save & Connect"}
            </button>
            <span className="text-xs text-zinc-500">
              Credentials are validated with Alpaca before being saved.
            </span>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 max-w-md rounded-lg border px-4 py-3 font-mono text-sm shadow-2xl ${
            toast.kind === "ok"
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
              : "border-rose-500/40 bg-rose-500/10 text-rose-200"
          }`}
        >
          {toast.msg}
        </div>
      )}

      {/* Help */}
      <details className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
        <summary className="cursor-pointer text-sm font-semibold text-zinc-300">
          Where do I get API keys?
        </summary>
        <ol className="mt-3 list-inside list-decimal space-y-1 text-sm text-zinc-400">
          <li>
            Sign up at{" "}
            <a
              href="https://app.alpaca.markets/signup"
              target="_blank"
              rel="noreferrer"
              className="text-emerald-400 underline"
            >
              app.alpaca.markets
            </a>{" "}
            (free, paper account is instant — no funding required).
          </li>
          <li>
            Open the{" "}
            <a
              href="https://app.alpaca.markets/paper/dashboard/overview"
              target="_blank"
              rel="noreferrer"
              className="text-emerald-400 underline"
            >
              paper dashboard
            </a>
            .
          </li>
          <li>
            On the right side, find the "API Keys" panel → "Generate New Key".
          </li>
          <li>
            Copy <strong>both</strong> the key (PK...) and the secret. The
            secret is shown <strong className="text-amber-300">only once</strong>.
          </li>
          <li>Paste them above and click "Save & Connect".</li>
        </ol>
      </details>
    </div>
  );
}

/* ───────── Sub-components ───────── */

function BackendBadge({ up }: { up: boolean | null }) {
  if (up === null)
    return (
      <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 font-mono text-[11px] text-zinc-400">
        checking…
      </span>
    );
  return up ? (
    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 font-mono text-[11px] text-emerald-300">
      ● backend up
    </span>
  ) : (
    <span className="rounded-full border border-rose-500/30 bg-rose-500/10 px-2.5 py-1 font-mono text-[11px] text-rose-300">
      ● backend offline
    </span>
  );
}

function ConnectionCard({
  status,
  account,
  onTest,
  onDisconnect,
  testing,
}: {
  status: ConnectionStatus | null;
  account: AlpacaAccount | null;
  onTest: () => void;
  onDisconnect: () => void;
  testing: boolean;
}) {
  if (!status?.connected) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full bg-zinc-600" />
          <p className="text-sm text-zinc-400">
            No Alpaca credentials saved yet.
          </p>
        </div>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
          <span className="text-sm font-semibold text-emerald-300">
            Connected to Alpaca
          </span>
          <span
            className={`rounded-full px-2 py-0.5 font-mono text-[10px] ${
              status.mode === "paper"
                ? "bg-emerald-500/15 text-emerald-300"
                : "bg-rose-500/15 text-rose-300"
            }`}
          >
            {status.mode?.toUpperCase()}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onTest}
            disabled={testing}
            className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
          >
            {testing ? "Testing..." : "Test Connection"}
          </button>
          <button
            onClick={onDisconnect}
            className="rounded-md border border-zinc-700 px-3 py-1.5 text-xs font-semibold text-zinc-400 transition hover:border-rose-500/50 hover:text-rose-300"
          >
            Disconnect
          </button>
        </div>
      </div>

      <div className="mb-4 font-mono text-xs text-zinc-500">
        api key: <span className="text-zinc-300">{status.api_key_masked}</span>
      </div>

      {account && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="Account #" value={account.account_number} mono />
          <Stat
            label="Cash"
            value={`$${account.cash.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
            accent
          />
          <Stat
            label="Equity"
            value={`$${account.equity.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
            accent
          />
          <Stat
            label="Buying Power"
            value={`$${account.buying_power.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
          />
        </div>
      )}

      {account && (account.trading_blocked || account.account_blocked) && (
        <p className="mt-3 rounded bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          ⚠ Account flag — trading_blocked={String(account.trading_blocked)}{" "}
          / account_blocked={String(account.account_blocked)}
        </p>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  mono,
  accent,
}: {
  label: string;
  value: string;
  mono?: boolean;
  accent?: boolean;
}) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
      <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p
        className={`mt-1 ${mono ? "font-mono text-xs" : "font-mono text-base"} ${
          accent ? "text-emerald-300" : "text-zinc-100"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
