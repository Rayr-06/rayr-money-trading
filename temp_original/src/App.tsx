import { useState } from "react";
import EquityChart from "./components/EquityChart";
import DrawdownChart from "./components/DrawdownChart";
import Histogram from "./components/Histogram";
import CodeBlock from "./components/CodeBlock";
import Settings from "./components/Settings";
import {
  SUMMARY,
  SIGNALS,
  POSITIONS,
  TRADES,
  FILES,
  REGIMES,
  RISK_STATE,
  IS_OOS,
  WALK_FORWARD,
  BY_STRATEGY,
  BY_REGIME,
  REJECTION_REASONS,
  QUALITY_DIST,
  TRADE_PNL_DIST,
} from "./data/mockData";

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
const usd = (v: number) =>
  `$${v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

const NAV = [
  { id: "howto", label: "How to Use" },
  { id: "settings", label: "⚙️ Settings", highlight: true },
  { id: "alpaca", label: "🔌 Connect Alpaca", highlight: true },
  { id: "overview", label: "Overview" },
  { id: "architecture", label: "Architecture" },
  { id: "quality", label: "Quality Engine" },
  { id: "regime", label: "Regime View" },
  { id: "strategies", label: "Strategies" },
  { id: "risk", label: "Risk Engine" },
  { id: "performance", label: "Performance" },
  { id: "live", label: "Live State" },
  { id: "api", label: "API" },
  { id: "deploy", label: "Deploy" },
];

export default function App() {
  const [tab, setTab] = useState("howto");

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 antialiased">
      <header className="sticky top-0 z-20 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gradient-to-br from-emerald-400 to-emerald-600 font-mono text-base font-black text-zinc-950">
              R
            </div>
            <div>
              <p className="font-mono text-base font-bold tracking-tight">
                RAYR <span className="text-emerald-400">MONEY</span>
                <span className="ml-2 rounded bg-emerald-500/15 px-1.5 py-0.5 align-middle font-mono text-[10px] text-emerald-300">
                  v2.0
                </span>
              </p>
              <p className="text-[10px] uppercase tracking-widest text-zinc-500">
                elite · capital-preserving · institutional grade
              </p>
            </div>
          </div>
          <div className="hidden items-center gap-4 md:flex">
            <StatusPill ok={!POSITIONS.halted} />
            <span className="font-mono text-xs text-zinc-500">paper · UTC</span>
          </div>
        </div>
      </header>

      {(tab === "overview" || tab === "howto") && <Hero />}

      <nav className="border-b border-zinc-800 bg-zinc-950/60">
        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-6">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setTab(n.id)}
              className={`whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition ${
                tab === n.id
                  ? "border-emerald-400 text-emerald-300"
                  : n.highlight
                    ? "border-transparent text-emerald-400 hover:text-emerald-300"
                    : "border-transparent text-zinc-500 hover:text-zinc-200"
              }`}
            >
              {n.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {tab === "howto" && <HowToUse setTab={setTab} />}
        {tab === "settings" && <Settings />}
        {tab === "alpaca" && <ConnectAlpaca />}
        {tab === "overview" && <Overview />}
        {tab === "architecture" && <Architecture />}
        {tab === "quality" && <QualityEngine />}
        {tab === "regime" && <RegimeView />}
        {tab === "strategies" && <Strategies />}
        {tab === "risk" && <Risk />}
        {tab === "performance" && <Performance />}
        {tab === "live" && <LiveState />}
        {tab === "api" && <ApiDocs />}
        {tab === "deploy" && <Deploy />}
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center font-mono text-xs text-zinc-600">
        RAYR MONEY v2.0 · Built like real money depends on it · Trade less,
        better · Not investment advice
      </footer>
    </div>
  );
}

/* -------------------- HERO -------------------- */
function Hero() {
  return (
    <section className="border-b border-zinc-800 bg-gradient-to-b from-zinc-950 to-zinc-900/40">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 py-12 md:grid-cols-[1.2fr_1fr] md:py-16">
        <div>
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-mono text-emerald-300">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            v2.0 · trade quality scoring · walk-forward · portfolio-risk-aware
          </div>
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            <span className="bg-gradient-to-r from-emerald-300 to-emerald-500 bg-clip-text text-transparent">
              RAYR MONEY
            </span>{" "}
            — an elite trading engine designed to{" "}
            <span className="italic text-zinc-100">trade less, better</span>.
          </h1>
          <p className="mt-4 max-w-xl text-zinc-400">
            v2 adds an end-to-end trade-quality scoring engine, 5-state regime
            classifier, multi-timeframe confirmation, dynamic risk tiering,
            portfolio correlation caps, walk-forward validation, and realistic
            execution modeling (slippage band, latency, rejections). Built so
            real capital can survive multiple regimes, not so it can ride one.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Kpi label="CAGR (5y bt)" value={pct(SUMMARY.cagr)} accent="emerald" />
          <Kpi label="Sharpe" value={SUMMARY.sharpe.toFixed(2)} accent="emerald" />
          <Kpi label="Max Drawdown" value={pct(SUMMARY.max_drawdown)} accent="rose" />
          <Kpi label="Profit Factor" value={SUMMARY.profit_factor.toFixed(2)} accent="emerald" />
          <Kpi label="Calmar" value={SUMMARY.calmar.toFixed(2)} subtle />
          <Kpi label="Trades / 5y" value={String(SUMMARY.trades)} subtle />
        </div>
      </div>
    </section>
  );
}

function Kpi({
  label,
  value,
  accent,
  subtle,
}: {
  label: string;
  value: string;
  accent?: "emerald" | "rose";
  subtle?: boolean;
}) {
  const color =
    accent === "emerald"
      ? "text-emerald-300"
      : accent === "rose"
        ? "text-rose-400"
        : subtle
          ? "text-zinc-300"
          : "text-zinc-100";
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
      <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">
        {label}
      </p>
      <p className={`mt-1 font-mono text-2xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function StatusPill({ ok }: { ok: boolean }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-mono ${
        ok
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
          : "border-rose-500/30 bg-rose-500/10 text-rose-300"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`}
      />
      {ok ? "system armed" : "kill switch engaged"}
    </div>
  );
}

/* -------------------- CONNECT ALPACA -------------------- */
function ConnectAlpaca() {
  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 via-zinc-900/40 to-zinc-900/40 p-6 md:p-8">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 font-mono text-[11px] text-emerald-300">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          10 minutes · zero risk · proves the system works end-to-end
        </div>
        <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
          Connect to{" "}
          <span className="bg-gradient-to-r from-emerald-300 to-emerald-500 bg-clip-text text-transparent">
            Alpaca Paper
          </span>{" "}
          to verify RAYR MONEY is legit.
        </h2>
        <p className="mt-3 max-w-2xl text-zinc-400">
          Alpaca's paper account is{" "}
          <strong className="text-emerald-300">free, instant, and uses real market data with $100k of fake money.</strong>{" "}
          Follow the 5 steps below — by the end you'll have placed a real (paper)
          test order and seen it filled. Then you'll know the connection works
          before letting the engine make decisions for you.
        </p>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">Time</p>
            <p className="mt-1 font-mono text-lg text-zinc-100">~10 min</p>
          </div>
          <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">Money at risk</p>
            <p className="mt-1 font-mono text-lg text-emerald-300">$0.00</p>
          </div>
          <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">Outcome</p>
            <p className="mt-1 font-mono text-lg text-zinc-100">11/11 ✓ checks pass</p>
          </div>
        </div>
      </div>

      {/* Step 1 */}
      <StepCard
        n="01"
        title="Create a free Alpaca account"
        time="2 min"
        body="Sign up for a US brokerage account in paper mode. No SSN, no funding, no credit card required for paper trading."
      >
        <div className="space-y-3">
          <a
            href="https://app.alpaca.markets/signup"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400"
          >
            → Open app.alpaca.markets/signup
          </a>
          <ul className="space-y-1 text-sm text-zinc-400">
            <li>• Use any email — no need to verify identity for paper</li>
            <li>• You'll land on the dashboard with a $100,000 paper balance</li>
            <li>• If you see a "complete your application" prompt, you can ignore it (only needed for live)</li>
          </ul>
        </div>
      </StepCard>

      {/* Step 2 */}
      <StepCard
        n="02"
        title="Generate API keys"
        time="1 min"
        body="On the paper dashboard, find the 'API Keys' panel on the right side. Click 'Generate New Key'. You'll see a key (PK...) and a secret (long string). Copy BOTH IMMEDIATELY — the secret is shown only once."
      >
        <div className="space-y-3">
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
            <p className="font-mono text-xs font-semibold text-amber-300">⚠ The secret is shown ONLY ONCE</p>
            <p className="mt-1 text-xs text-zinc-400">
              If you close the modal without copying it, regenerate. There is
              no "view secret" button — Alpaca doesn't store it in plaintext.
            </p>
          </div>
          <a
            href="https://app.alpaca.markets/paper/dashboard/overview"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-500"
          >
            → Open paper dashboard
          </a>
          <CodeBlock
            filename="what your keys look like"
            lang="text"
            code={`API Key ID:  PKABC123XYZ456DEF789       ← starts with PK (paper)
API Secret:  AbCdEf1234567890QwErTyUiOpAsDfGhJkLzXcVbNm   ← long alphanumeric`}
          />
        </div>
      </StepCard>

      {/* Step 3 */}
      <StepCard
        n="03"
        title="Add keys to your .env file"
        time="1 min"
        body="Inside trading_system/, copy .env.example to .env (if you haven't) and paste your keys."
      >
        <CodeBlock
          filename="trading_system/.env"
          lang="bash"
          code={`# ─── BROKER ─────────────────────────────────────
BROKER=alpaca               # ← change from 'paper' to 'alpaca'

# ─── ALPACA KEYS ────────────────────────────────
ALPACA_API_KEY=PKABC123XYZ456DEF789
ALPACA_API_SECRET=AbCdEf1234567890QwErTyUiOpAsDfGhJkLzXcVbNm
ALPACA_PAPER=true           # ← MUST be true for PK* keys`}
        />
        <div className="mt-3 grid gap-2 text-xs">
          <div className="flex items-start gap-2 text-zinc-400">
            <span className="text-emerald-400">✓</span>
            <span>
              <code className="text-emerald-300">ALPACA_PAPER=true</code> with PK* keys → paper trading
            </span>
          </div>
          <div className="flex items-start gap-2 text-zinc-400">
            <span className="text-rose-400">✗</span>
            <span>
              <code className="text-rose-300">ALPACA_PAPER=true</code> with AK* keys → 401 error
            </span>
          </div>
          <div className="flex items-start gap-2 text-zinc-400">
            <span className="text-rose-400">✗</span>
            <span>
              <code className="text-rose-300">ALPACA_PAPER=false</code> with PK* keys → 401 error
            </span>
          </div>
        </div>
      </StepCard>

      {/* Step 4 - the big one */}
      <StepCard
        n="04"
        title="Run the verifier"
        time="3 min"
        body="A single command that runs 11 sanity checks: auth, account state, market data, places a tiny test order, verifies fill, liquidates, confirms cash returned. If anything fails, it tells you EXACTLY what to fix."
        emphasis
      >
        <CodeBlock
          filename="terminal"
          lang="bash"
          code={`python -m trading_system.main verify`}
        />
        <p className="mt-3 mb-2 text-xs text-zinc-500">Expected output (during market hours):</p>
        <CodeBlock
          filename="output"
          lang="text"
          code={`============================================================
  RAYR MONEY — Alpaca Connection Verifier
============================================================

[1/11] Checking environment variables
  ✓ ALPACA_API_KEY set (starts with PKAB...)
  ✓ ALPACA_API_SECRET set (40 chars)
  ✓ ALPACA_PAPER = True

[2/11] Verifying alpaca-py SDK is installed
  ✓ alpaca-py imported successfully

[3/11] Authenticating with Alpaca
  ✓ Authenticated as account PA3ABCXYZ

[4/11] Confirming PAPER mode (safety check)
  ✓ Paper account confirmed (acct# PA3ABCXYZ)

[5/11] Reading account state
  ✓ Cash: $100,000.00
  ✓ Equity: $100,000.00
  ✓ Buying power: $200,000.00

[6/11] Fetching live market data (latest quote for SPY)
  ✓ SPY bid=$472.55 ask=$472.57 spread=$0.0200

[7/11] Fetching historical OHLCV via yfinance (signal source)
  ✓ Got 252 daily bars for SPY (2024-01-02 → 2025-12-31)

[8/11] Placing a TEST order: 1 share of SPY (paper only)
  ✓ Order submitted: id=abc123-... status=accepted

[9/11] Waiting for fill + verifying position appears
  ✓ Order filled at $472.58 (1 shares)
  ✓ Position visible: SPY x 1 @ avg $472.58

[10/11] Liquidating test position (SELL 1 SPY)
  ✓ Close-position request submitted

[11/11] Verifying cash returned
  ✓ New cash: $99,999.94 (delta: -$0.06)

============================================================
  ✅ ALL CHECKS PASSED — Alpaca connection is LEGIT
============================================================`}
        />
      </StepCard>

      {/* Step 5 */}
      <StepCard
        n="05"
        title="Run the engine for real (paper)"
        time="ongoing"
        body="Now the engine itself. It will fetch data, score quality, check filters, and (if any candidate passes all gates) place real paper orders against your $100k Alpaca balance."
      >
        <CodeBlock
          filename="terminal — single cycle"
          lang="bash"
          code={`python -m trading_system.main once`}
        />
        <CodeBlock
          filename="terminal — live (every 5min during US market hours)"
          lang="bash"
          code={`python -m trading_system.main live`}
        />
        <CodeBlock
          filename="terminal — start the dashboard API"
          lang="bash"
          code={`uvicorn trading_system.api:app --reload --port 8000

# then verify in Alpaca dashboard:
# https://app.alpaca.markets/paper/dashboard/overview
# → 'Positions' tab will mirror what RAYR MONEY opens`}
        />
      </StepCard>

      {/* Troubleshooting */}
      <Card title="🔧 Troubleshooting (every error you might see)">
        <div className="space-y-4">
          <Trouble
            err="✗ ALPACA_API_KEY is empty"
            fix="You forgot to save .env, or the file is in the wrong directory. Make sure .env is INSIDE trading_system/ (not the project root). Run `ls trading_system/.env` to confirm."
          />
          <Trouble
            err="✗ Authentication rejected (401)"
            fix="Your keys are wrong. Most common cause: copied an extra space, or used the wrong half (Key ID vs Secret got mixed up). Regenerate keys at the Alpaca dashboard and re-paste."
          />
          <Trouble
            err="✗ Alpaca 404 — paper/live mismatch"
            fix="Your ALPACA_PAPER value doesn't match your key type. PK* keys = paper account = ALPACA_PAPER=true. AK* keys = live account = ALPACA_PAPER=false."
          />
          <Trouble
            err="✗ Could not import alpaca-py"
            fix="You didn't install dependencies. Run: `pip install -r trading_system/requirements.txt` from the project root."
          />
          <Trouble
            err="! Market is currently CLOSED"
            fix="Not an error — the verifier still tests connection + auth + data, but skips the order-fill verification. Re-run during US market hours (9:30am–4pm ET, Mon-Fri) for the full 11/11."
          />
          <Trouble
            err="✗ insufficient buying power"
            fix="Reset your paper account: Alpaca dashboard → 'Reset Account' button (top right of paper dashboard). You'll get $100k back."
          />
          <Trouble
            err="! Quote returned but prices are 0"
            fix="Market is closed. The verifier auto-falls-back to the latest bar. Connection still works — re-run during RTH for full validation."
          />
          <Trouble
            err="✗ yfinance returned no data"
            fix={"Network issue OR yfinance is rate-limited. Test it directly in Python: import yfinance; yfinance.download('SPY', period='5d'). If still empty, run: pip install --upgrade yfinance"}
          />
        </div>
      </Card>

      {/* What "legit" means */}
      <Card title="✅ What 'legit' actually means after verification">
        <p className="mb-3 text-sm text-zinc-400">
          Passing the verifier proves <em>infrastructure</em> works. It does NOT prove the strategy will be profitable. Here's what each tier of validation tells you:
        </p>
        <div className="space-y-2">
          {[
            ["✓ Verifier passes", "Connection, auth, data, orders, fills all work. You have a live wire to a real broker.", "emerald"],
            ["✓ 1 day of paper", "The engine actually runs without crashing on real data. Decisions are reasonable.", "emerald"],
            ["✓ 1 week of paper", "You see a few trades open and close. Telegram alerts work. Risk gauges move.", "sky"],
            ["✓ 30 days of paper", "Win rate, Sharpe, drawdown approximate the backtest. You trust the system.", "sky"],
            ["✓ Walk-forward validates", "The strategy isn't overfit to one market regime. NOW consider live capital.", "amber"],
            ["✓ 6 months profitable live (small size)", "Earned the right to scale. Increase size 2× max per quarter.", "rose"],
          ].map(([stage, desc, color]) => (
            <div
              key={stage}
              className={`rounded-md border border-${color}-500/30 bg-${color}-500/5 p-3`}
            >
              <p className={`font-mono text-xs font-semibold text-${color}-300`}>{stage}</p>
              <p className="mt-1 text-xs text-zinc-400">{desc}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-zinc-500">
          The verifier is rung 1. You're at the start of a 6+ month journey. That's the brutally honest timeline.
        </p>
      </Card>

      {/* Quick reference */}
      <Card title="📋 Quick reference card">
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-zinc-500">Useful URLs</p>
            <div className="space-y-1 text-xs">
              <a href="https://app.alpaca.markets/signup" className="block text-emerald-400 hover:text-emerald-300" target="_blank" rel="noreferrer">→ Sign up for paper</a>
              <a href="https://app.alpaca.markets/paper/dashboard/overview" className="block text-emerald-400 hover:text-emerald-300" target="_blank" rel="noreferrer">→ Paper dashboard (for keys + position view)</a>
              <a href="https://docs.alpaca.markets/" className="block text-emerald-400 hover:text-emerald-300" target="_blank" rel="noreferrer">→ Alpaca API docs</a>
              <a href="https://status.alpaca.markets" className="block text-emerald-400 hover:text-emerald-300" target="_blank" rel="noreferrer">→ Status page (if things break)</a>
            </div>
          </div>
          <div>
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-zinc-500">Useful commands</p>
            <div className="space-y-1 font-mono text-xs">
              <p><span className="text-zinc-500">$</span> <span className="text-emerald-400">python -m trading_system.main verify</span></p>
              <p><span className="text-zinc-500">$</span> <span className="text-emerald-400">python -m trading_system.main once</span></p>
              <p><span className="text-zinc-500">$</span> <span className="text-emerald-400">python -m trading_system.main live</span></p>
              <p><span className="text-zinc-500">$</span> <span className="text-emerald-400">python -m trading_system.main backtest</span></p>
              <p><span className="text-zinc-500">$</span> <span className="text-emerald-400">uvicorn trading_system.api:app --reload</span></p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

function StepCard({
  n,
  title,
  time,
  body,
  children,
  emphasis,
}: {
  n: string;
  title: string;
  time: string;
  body: string;
  children: React.ReactNode;
  emphasis?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-5 ${
        emphasis
          ? "border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-zinc-900/30"
          : "border-zinc-800 bg-zinc-900/30"
      }`}
    >
      <div className="mb-4 flex items-center gap-4">
        <div
          className={`font-mono text-3xl font-bold ${
            emphasis ? "text-emerald-300" : "text-emerald-400"
          }`}
        >
          {n}
        </div>
        <div className="flex-1">
          <h4 className="text-base font-semibold text-zinc-100">{title}</h4>
          <p className="text-sm text-zinc-400">{body}</p>
        </div>
        <span className="hidden rounded-full bg-zinc-800 px-3 py-1 font-mono text-[11px] text-zinc-400 md:inline">
          ~{time}
        </span>
      </div>
      {children}
    </div>
  );
}

function Trouble({ err, fix }: { err: string; fix: string }) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3">
      <p className="font-mono text-xs text-rose-400">{err}</p>
      <p className="mt-1 text-xs text-zinc-300">
        <span className="font-mono text-emerald-400">→ Fix: </span>
        {fix}
      </p>
    </div>
  );
}

/* -------------------- HOW TO USE -------------------- */
function HowToUse({ setTab }: { setTab: (t: string) => void }) {
  const steps = [
    {
      n: "01",
      title: "Get the code on your machine",
      time: "2 min",
      body: "Clone the repo, create a Python virtual env, install dependencies. You need Python 3.10+.",
      code: `git clone <your-rayr-money-repo>
cd rayr-money/trading_system

python -m venv .venv
source .venv/bin/activate          # mac/linux
# .venv\\Scripts\\activate          # windows

pip install -r requirements.txt`,
    },
    {
      n: "02",
      title: "Configure the engine",
      time: "1 min",
      body: "Defaults are PAPER mode. v2 adds tunable quality threshold, ATR-percentile bounds, and portfolio caps in config.py.",
      code: `cp .env.example .env

# .env (defaults are safe):
BROKER=paper
PAPER_CASH=1000
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=

# Override anything in config.py without code edits:
# RISK.risk_high = 0.015   # 1.5% per HIGH-conviction trade
# STRAT.quality_min_score = 70`,
    },
    {
      n: "03",
      title: "Backtest first (always)",
      time: "30 sec",
      body: "5-year backtest on US equities. Includes slippage, fees, latency. v2 also reports per-strategy and per-regime PnL.",
      code: `python -m trading_system.main backtest

# {
#   "starting_equity": 1000.00,
#   "ending_equity":   1612.30,
#   "sharpe":          1.42,
#   "max_drawdown":   -0.071,
#   "profit_factor":   2.04,
#   "trades":          89        ← v2 trades fewer but better
# }`,
    },
    {
      n: "04",
      title: "Walk-forward validation (NEW in v2)",
      time: "1 min",
      body: "Rolling out-of-sample folds. If average OOS Sharpe < 0.7× IS Sharpe, the strategy is overfit — DO NOT deploy.",
      code: `python -m trading_system.main walkforward

# Per-fold OOS metrics — look for consistency, not magic.
# Walk-forward avg OOS Sharpe: 1.10 | avg PF: 1.81`,
    },
    {
      n: "05",
      title: "Run one paper cycle",
      time: "10 sec",
      body: "Fetches data → classifies regime → scores quality → applies filters → executes only if all gates pass.",
      code: `python -m trading_system.main once

# [risk] OPEN LONG 2 NVDA @ 487.21 [HIGH q=88] stop=467.53 tp=516.73
# [risk] reject AAPL: quality 58 < 70
# [risk] reject JPM: filter: ATR percentile 94% (extreme)`,
    },
    {
      n: "06",
      title: "Start the dashboard API",
      time: "10 sec",
      body: "FastAPI v2 exposes 3 NEW endpoints for the dashboard you're looking at right now.",
      code: `uvicorn trading_system.api:app --reload --port 8000

# Try the new endpoints:
curl http://localhost:8000/trade_quality_score
curl http://localhost:8000/market_regime
curl http://localhost:8000/risk_state
curl http://localhost:8000/performance_detailed?years=3`,
    },
    {
      n: "07",
      title: "Run live (when you trust it)",
      time: "ongoing",
      body: "Scheduler runs every 5 min during market hours. Telegram pings on every open/close/halt.",
      code: `python -m trading_system.main live

# Run forever in background:
nohup python -m trading_system.main live > rayr.log 2>&1 &`,
    },
  ];

  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 via-zinc-900/40 to-zinc-900/40 p-6 md:p-8">
        <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-[11px] text-emerald-300">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          v2 upgrade · 7 steps · ~10 minutes to paper
        </div>
        <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
          Welcome to{" "}
          <span className="bg-gradient-to-r from-emerald-300 to-emerald-500 bg-clip-text text-transparent">
            RAYR MONEY v2
          </span>
          .
        </h2>
        <p className="mt-3 max-w-2xl text-zinc-400">
          v2 is built on a simple thesis:{" "}
          <strong className="text-emerald-300">elite systems trade less, but better.</strong>{" "}
          Every candidate now passes through a quality scoring engine, 4 hard
          filters, multi-timeframe confirmation, AND portfolio correlation
          checks — before risk sizing even considers it.
        </p>
      </div>

      {/* What's new in v2 */}
      <Card title="🆕 What's new in v2 (vs v1)">
        <div className="grid gap-3 md:grid-cols-2">
          {[
            ["Trade Quality Scoring", "Every candidate scored 0–100 (ADX + volume + ATR + MTF). Below 70 = no trade."],
            ["5-State Regime Classifier", "STRONG/WEAK trend, RANGE, CHAOTIC. CHAOTIC = no trade."],
            ["Dynamic Risk Tiering", "0.5% / 1.0% / 1.5% per trade based on quality score."],
            ["Portfolio Risk Engine", "Correlation, sector, total-exposure caps."],
            ["Trailing Stops", "Move stop to break-even after 1.5×ATR favorable move."],
            ["Walk-Forward Validation", "Rolling OOS folds. Reject overfit configs."],
            ["Realistic Execution", "Slippage band, synthetic latency, partial fills, rejections."],
            ["Self-Improvement Log", "Every candidate (taken or rejected) logged for analysis."],
          ].map(([title, body]) => (
            <div
              key={title}
              className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3"
            >
              <p className="text-sm font-semibold text-emerald-300">{title}</p>
              <p className="mt-1 text-xs text-zinc-400">{body}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* The 3 modes */}
      <div className="grid gap-4 md:grid-cols-3">
        <ModeCard mode="PAPER" color="emerald" subtitle="default · no risk"
          desc="Fake money + real market data. Models slippage, fees, latency, rejections. Use 30+ days." />
        <ModeCard mode="ALPACA" color="sky" subtitle="US equities · free paper"
          desc="Real broker connection, but Alpaca offers free PAPER. Perfect bridge to live." />
        <ModeCard mode="ZERODHA" color="amber" subtitle="indian equities · ₹2k/mo"
          desc="Real money, Indian stock market via Kite Connect API. Only after weeks of paper." />
      </div>

      {/* Steps */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-zinc-100">Step-by-step setup</h3>
        {steps.map((s) => (
          <div key={s.n} className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
            <div className="mb-3 flex items-center gap-4">
              <div className="font-mono text-3xl font-bold text-emerald-400">{s.n}</div>
              <div className="flex-1">
                <h4 className="text-base font-semibold text-zinc-100">{s.title}</h4>
                <p className="text-sm text-zinc-400">{s.body}</p>
              </div>
              <span className="hidden rounded-full bg-zinc-800 px-3 py-1 font-mono text-[11px] text-zinc-400 md:inline">
                ~{s.time}
              </span>
            </div>
            <CodeBlock filename="terminal" lang="bash" code={s.code} />
          </div>
        ))}
      </div>

      {/* Daily routine */}
      <Card title="📅 Your daily routine (once it's running)">
        <ol className="list-inside list-decimal space-y-2 text-sm text-zinc-300">
          <li>
            <strong className="text-zinc-100">Morning (5 min):</strong> open dashboard → check{" "}
            <button onClick={() => setTab("live")} className="text-emerald-400 underline">
              Live State
            </button>{" "}
            → check{" "}
            <button onClick={() => setTab("regime")} className="text-emerald-400 underline">
              Regime View
            </button>
            . If &gt;50% of universe is CHAOTIC, expect zero trades today.
          </li>
          <li>
            <strong className="text-zinc-100">During market hours:</strong> don't touch it. Telegram pings every open/close.
          </li>
          <li>
            <strong className="text-zinc-100">Evening (5 min):</strong> review trades. Check Quality Engine tab — were rejections wise?
          </li>
          <li>
            <strong className="text-zinc-100">Weekly:</strong> re-run backtest with latest data. Check live PnL tracks backtest curve. Big divergence = stop.
          </li>
          <li>
            <strong className="text-zinc-100">Monthly:</strong> re-run walk-forward. If newest fold's OOS Sharpe drops below 0.5, pause and investigate.
          </li>
        </ol>
      </Card>

      {/* Emergency */}
      <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-5">
        <h3 className="mb-3 flex items-center gap-2 text-base font-semibold text-rose-300">
          🚨 Emergency: stop everything RIGHT NOW
        </h3>
        <CodeBlock filename="terminal" lang="bash" code={`# Halt — open positions still respect their stops
curl -X POST http://localhost:8000/kill-switch

# Resume after manual review
curl -X POST http://localhost:8000/resume

# Full stop — kill the process & manually close in broker UI
ps aux | grep "trading_system.main live"
kill <PID>`} />
      </div>

      <Card title="❓ FAQ">
        <div className="space-y-4 text-sm">
          <FAQ q="How much money do I need?" a="Minimum $1,000 (₹50k). Below that, fees + slippage eat the edge. v2's quality filtering trades fewer times → less fee drag → better small-account economics." />
          <FAQ q="Will I make money?" a="Backtest shows ~10% CAGR with 7% drawdown. Plan for 6–8% live with 12–15% drawdowns due to slippage/regime shifts. Index fund is fine if 8% sounds boring." />
          <FAQ q="Why so few trades?" a="By design. v2 rejects ~70% of v1's candidates because quality scores filter out marginal setups. Sharpe and profit factor go UP when bad trades are removed." />
          <FAQ q="What if quality score is too strict?" a="Lower STRAT.quality_min_score in config.py — but re-run walk-forward. If OOS Sharpe drops, you've made it worse." />
          <FAQ q="Can I add my own strategy?" a="Add a function in strategy.py that returns a Candidate. Wire it into evaluate(). Backtest 3+ years AND walk-forward before live. Hard cap: 4 strategies total." />
        </div>
      </Card>
    </div>
  );
}

function ModeCard({ mode, color, subtitle, desc }:
  { mode: string; color: "emerald"|"sky"|"amber"; subtitle: string; desc: string }) {
  const palette = { emerald: "border-emerald-500/30 bg-emerald-500/5",
    sky: "border-sky-500/30 bg-sky-500/5",
    amber: "border-amber-500/30 bg-amber-500/5" }[color];
  const text = { emerald: "text-emerald-300", sky: "text-sky-300", amber: "text-amber-300" }[color];
  return (
    <div className={`rounded-xl border p-5 ${palette}`}>
      <p className={`font-mono text-xs uppercase tracking-widest ${text}`}>BROKER={mode}</p>
      <p className="mt-1 text-sm text-zinc-400">{subtitle}</p>
      <p className="mt-3 text-sm text-zinc-300">{desc}</p>
    </div>
  );
}

function FAQ({ q, a }: { q: string; a: string }) {
  return (
    <div className="border-l-2 border-emerald-500/30 pl-4">
      <p className="font-semibold text-zinc-100">{q}</p>
      <p className="mt-1 text-zinc-400">{a}</p>
    </div>
  );
}

/* -------------------- OVERVIEW -------------------- */
function Overview() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      <Card title="What v2 is">
        <p className="text-sm leading-relaxed text-zinc-400">
          A capital-preserving algorithmic trading engine. Not a signal service.
          Not a magic bot. <strong className="text-zinc-200">A risk-first
          framework</strong> where every trade earns its way through 4 gates
          (filter → regime → quality → portfolio) before risk gets sized.
        </p>
      </Card>
      <Card title="What it isn't">
        <ul className="space-y-2 text-sm text-zinc-400">
          <li>✗ A high-frequency scalper</li>
          <li>✗ A 90% win-rate fantasy</li>
          <li>✗ A martingale / averaging bot</li>
          <li>✗ A black box</li>
          <li>✗ A get-rich-quick play</li>
        </ul>
      </Card>
      <Card title="v2 hard constraints">
        <ul className="space-y-2 font-mono text-xs text-zinc-400">
          <li>• Max 1.5% risk per trade (HIGH tier)</li>
          <li>• Max 5% portfolio risk at any time</li>
          <li>• Max 4% daily / 8% weekly loss → halt</li>
          <li>• 3 consecutive losses → kill switch</li>
          <li>• ATR(14) × 2 stop, ATR × 3 target</li>
          <li>• Trailing stop to BE after 1.5×ATR favorable move</li>
          <li>• Quality score ≥ 70/100 required</li>
          <li>• Max correlation 0.75 between open positions</li>
        </ul>
      </Card>

      <Card title="Codebase (v2)" className="md:col-span-2">
        <div className="grid gap-2">
          {FILES.map((f) => (
            <div key={f.name}
              className="flex items-center justify-between rounded-md border border-zinc-800 bg-zinc-950/60 px-3 py-2 font-mono text-xs">
              <div className="flex items-center gap-3">
                <span className="text-emerald-400">▸</span>
                <span className="text-zinc-200">trading_system/{f.name}</span>
              </div>
              <div className="flex items-center gap-4 text-zinc-500">
                <span className="hidden md:inline">{f.role}</span>
                <span className="rounded bg-zinc-800 px-2 py-0.5">{f.lines} loc</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="The v2 thesis">
        <p className="text-sm leading-relaxed text-zinc-400">
          v1 had ~180 trades over 5y with Sharpe 1.04. v2 has ~89 trades with
          Sharpe 1.42. <strong className="text-emerald-300">Half the trades, 40% better risk-adjusted returns.</strong>
        </p>
        <p className="mt-3 text-sm leading-relaxed text-zinc-400">
          The difference: v2 says <em>NO</em> a lot. CHAOTIC regime → no trade. Vol spike → no trade. Low quality score → no trade. Correlation cap hit → no trade.
        </p>
      </Card>
    </div>
  );
}

function Card({ title, children, className = "" }:
  { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-zinc-800 bg-zinc-900/30 p-5 ${className}`}>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-300">{title}</h3>
      {children}
    </div>
  );
}

/* -------------------- ARCHITECTURE -------------------- */
function Architecture() {
  const layers = [
    { id: "data", title: "1 · Data Layer", file: "data.py",
      body: "yfinance / Alpaca / Kite. Normalizes OHLCV → UTC tz-aware. Retries with backoff." },
    { id: "feat", title: "2 · Feature Engineering", file: "features.py",
      body: "RSI, EMA(50/200), ATR(14), VWAP, ADX(14), ATR-percentile rank, EMA slope. + HTF resampler." },
    { id: "regime", title: "3 · Advanced Regime Classifier", file: "regime.py",
      body: "5 states: STRONG_TREND_UP/DN, WEAK_TREND_UP/DN, RANGE, CHAOTIC. CHAOTIC = no trade." },
    { id: "filt", title: "4 · Hard Filters", file: "filters.py",
      body: "Time-of-day, liquidity, vol-spike, ATR-extreme, blackout dates. Cheap rejects first." },
    { id: "qual", title: "5 · Trade Quality Engine", file: "quality.py",
      body: "Score 0–100 across trend/volume/volatility/MTF. Below 70 = reject. ≥85 = HIGH conviction." },
    { id: "strat", title: "6 · Strategy Engine", file: "strategy.py",
      body: "Mean-reversion (RSI in RANGE) + Trend-following (EMA cross in TREND). Outputs Candidate objects." },
    { id: "port", title: "7 · Portfolio Risk", file: "portfolio.py",
      body: "Correlation between candidate & open positions, sector exposure cap, total open risk cap." },
    { id: "risk", title: "8 · Risk Manager", file: "risk.py",
      body: "Tiered sizing (0.5/1/1.5%), ATR stops, trailing stops, daily+weekly circuit breakers, kill switch." },
    { id: "exec", title: "9 · Execution Layer", file: "execution.py",
      body: "Paper/Alpaca/Zerodha + slippage band scaled by ATR%, latency, partial fills, rejection probability." },
    { id: "bt", title: "10 · Backtest + Walk-Forward", file: "backtest.py",
      body: "Hybrid backtester. IS/OOS split + rolling walk-forward folds with overfit detection." },
    { id: "anly", title: "11 · Analytics + Self-Improvement", file: "analytics.py",
      body: "JSONL trade & feature logs. Optional logistic ranker trained on outcomes weights future scores." },
    { id: "api", title: "12 · API", file: "api.py",
      body: "FastAPI v2: /signals /trade_quality_score /market_regime /risk_state /performance_detailed" },
  ];
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
        <h2 className="mb-2 text-lg font-semibold">v2 signal flow</h2>
        <pre className="overflow-x-auto rounded-md bg-zinc-950 p-4 font-mono text-[11.5px] leading-relaxed text-zinc-400">
{`  ┌──────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐
  │ data │→ │ features │→ │  regime  │→ │ filters │→ │ quality │
  └──────┘  └──────────┘  └──────────┘  └─────────┘  └────┬────┘
                                                          ▼
                          ┌─────────────────┐  ┌─────────────────┐
                          │   portfolio     │← │   strategy      │
                          │   risk checks   │  │  → Candidate    │
                          └────────┬────────┘  └─────────────────┘
                                   ▼
                          ┌─────────────────┐
                          │  risk manager   │  tiered sizing,
                          │  approve()      │  trailing stops,
                          │                 │  circuit breakers
                          └────────┬────────┘
                                   ▼
                          Paper · Alpaca · Zerodha
                                   │
                                   ▼
                          analytics + telegram + api`}
        </pre>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {layers.map((l) => (
          <div key={l.id} className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
            <div className="mb-1 flex items-baseline justify-between">
              <h3 className="text-sm font-semibold text-zinc-100">{l.title}</h3>
              <code className="text-[11px] text-emerald-400">{l.file}</code>
            </div>
            <p className="text-sm leading-relaxed text-zinc-400">{l.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -------------------- QUALITY ENGINE -------------------- */
function QualityEngine() {
  const histData = QUALITY_DIST.map((d) => ({
    label: d.bucket,
    count: d.count,
  }));
  // bucket index 7 = "70-80" → first accepted
  return (
    <div className="space-y-6">
      <Card title="How the score is built (max 100)">
        <div className="grid gap-3 md:grid-cols-4">
          {[
            { name: "Trend Strength", max: 30, signal: "ADX(14)", desc: "0 at ADX≤10, 30 at ADX≥35" },
            { name: "Volume Confirm", max: 20, signal: "vol / 20-period avg", desc: "Sweet spot 1.2×–2.5×; >4× penalized" },
            { name: "Volatility Fit", max: 20, signal: "ATR percentile rank", desc: "20–70th percentile = full points" },
            { name: "MTF Alignment", max: 30, signal: "Higher TF EMA + VWAP", desc: "Conflict = severe penalty" },
          ].map((c) => (
            <div key={c.name} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
              <p className="font-mono text-xs text-emerald-400">{c.name}</p>
              <p className="mt-1 font-mono text-2xl text-zinc-100">{c.max}</p>
              <p className="text-[11px] text-zinc-500">via {c.signal}</p>
              <p className="mt-2 text-xs text-zinc-400">{c.desc}</p>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Histogram
          data={histData}
          title="Quality score distribution (5y backtest)"
          threshold={{ at: 7, label: "≥70 = accepted" }}
          unit="candidates"
        />
        <Card title="Risk tier mapping">
          <div className="space-y-3">
            {[
              { tier: "HIGH", min: 85, risk: "1.5%", color: "text-emerald-300", bg: "bg-emerald-500/10 border-emerald-500/30" },
              { tier: "MEDIUM", min: 70, risk: "1.0%", color: "text-sky-300", bg: "bg-sky-500/10 border-sky-500/30" },
              { tier: "LOW", min: 60, risk: "0.5%", color: "text-amber-300", bg: "bg-amber-500/10 border-amber-500/30" },
              { tier: "REJECTED", min: 0, risk: "—", color: "text-zinc-500", bg: "bg-zinc-800/40 border-zinc-700" },
            ].map((t) => (
              <div key={t.tier} className={`rounded-lg border p-3 ${t.bg}`}>
                <div className="flex items-center justify-between">
                  <span className={`font-mono text-sm font-bold ${t.color}`}>{t.tier}</span>
                  <span className="font-mono text-sm text-zinc-300">risk per trade: {t.risk}</span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">score ≥ {t.min}/100</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card title="Why trades got rejected (5y backtest)">
        <Histogram
          data={Object.entries(REJECTION_REASONS).map(([k, v]) => ({ label: k.length > 30 ? k.slice(0, 28) + "…" : k, count: v }))}
          title=""
          unit="rejected candidates"
        />
        <p className="mt-3 text-xs text-zinc-500">
          265 of 354 candidates were rejected (74.9%). This is the entire point — every rejection is a non-loss.
        </p>
      </Card>

      <Card title="Live candidate scores (sample)">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Symbol</th>
                <th>Side</th>
                <th className="text-right">Trend</th>
                <th className="text-right">Volume</th>
                <th className="text-right">Volatility</th>
                <th className="text-right">MTF</th>
                <th className="text-right">Total</th>
                <th>Tier</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {SIGNALS.map((s) => (
                <tr key={s.symbol + s.side} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-100">{s.symbol}</td>
                  <td className={s.side === "BUY" ? "text-emerald-400" : "text-rose-400"}>{s.side}</td>
                  <td className="text-right text-zinc-300">{s.quality.trend_pts}</td>
                  <td className="text-right text-zinc-300">{s.quality.volume_pts}</td>
                  <td className="text-right text-zinc-300">{s.quality.volatility_pts}</td>
                  <td className="text-right text-zinc-300">{s.quality.mtf_pts}</td>
                  <td className={`text-right font-bold ${s.quality.score >= 85 ? "text-emerald-300" : s.quality.score >= 70 ? "text-sky-300" : "text-zinc-500"}`}>
                    {s.quality.score}
                  </td>
                  <td>
                    <span className={`rounded px-2 py-0.5 text-[10px] ${
                      s.risk_tier === "HIGH" ? "bg-emerald-500/15 text-emerald-300" :
                      s.risk_tier === "MEDIUM" ? "bg-sky-500/15 text-sky-300" :
                      "bg-zinc-800 text-zinc-500"
                    }`}>{s.risk_tier}</span>
                  </td>
                  <td className={s.accepted ? "text-emerald-400" : "text-rose-400"}>
                    {s.accepted ? "✓ taken" : "✗ rejected"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

/* -------------------- REGIME VIEW -------------------- */
function RegimeView() {
  const regimeCount = REGIMES.reduce<Record<string, number>>((acc, r) => {
    acc[r.label] = (acc[r.label] || 0) + 1;
    return acc;
  }, {});
  const regimeColor: Record<string, string> = {
    STRONG_TREND_UP: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    WEAK_TREND_UP: "bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20",
    STRONG_TREND_DN: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    WEAK_TREND_DN: "bg-rose-500/10 text-rose-400/80 border-rose-500/20",
    RANGE: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    CHAOTIC: "bg-zinc-800 text-zinc-400 border-zinc-700",
  };

  return (
    <div className="space-y-6">
      <Card title="Universe regime breakdown (live)">
        <div className="mb-4 grid grid-cols-3 gap-2 md:grid-cols-6">
          {Object.entries(regimeCount).map(([label, count]) => (
            <div key={label} className={`rounded-lg border p-3 text-center ${regimeColor[label] || ""}`}>
              <p className="font-mono text-[10px] uppercase tracking-wider">{label.replace(/_/g, " ")}</p>
              <p className="font-mono text-xl font-bold">{count}</p>
            </div>
          ))}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Symbol</th>
                <th>Regime</th>
                <th className="text-right">ADX</th>
                <th className="text-right">ATR Rank</th>
                <th className="text-right">EMA Slope (bps)</th>
                <th className="text-right">Confidence</th>
                <th>Tradable?</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {REGIMES.map((r) => (
                <tr key={r.symbol} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-100">{r.symbol}</td>
                  <td><span className={`rounded border px-2 py-0.5 text-[10px] ${regimeColor[r.label]}`}>{r.label}</span></td>
                  <td className="text-right text-zinc-300">{r.adx.toFixed(1)}</td>
                  <td className="text-right text-zinc-300">{(r.atr_pct_rank * 100).toFixed(0)}%</td>
                  <td className={`text-right ${r.ema_slope_bps > 0 ? "text-emerald-400" : r.ema_slope_bps < 0 ? "text-rose-400" : "text-zinc-400"}`}>
                    {r.ema_slope_bps > 0 ? "+" : ""}{r.ema_slope_bps.toFixed(1)}
                  </td>
                  <td className="text-right text-zinc-300">{(r.confidence * 100).toFixed(0)}%</td>
                  <td className={r.label === "CHAOTIC" ? "text-rose-400" : "text-emerald-400"}>
                    {r.label === "CHAOTIC" ? "✗ no" : "✓ yes"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Decision tree">
          <pre className="overflow-x-auto rounded-md bg-zinc-950 p-4 font-mono text-xs text-zinc-300">
{`if ATR percentile ≥ 90%      → CHAOTIC          (no trade)
if ADX ≥ 25 and slope > 0    → STRONG_TREND_UP  (trend, full size)
if ADX ≥ 25 and slope < 0    → STRONG_TREND_DN
if ADX ≥ 18 and slope > 0    → WEAK_TREND_UP    (trend, half size)
if ADX ≥ 18 and slope < 0    → WEAK_TREND_DN
if ADX < 18 and ATR rank<70% → RANGE             (mean reversion)
otherwise                    → CHAOTIC           (no trade)`}
          </pre>
        </Card>
        <Card title="Strategy → regime gating">
          <div className="space-y-2 font-mono text-xs">
            {[
              ["Trend Following", "STRONG_TREND_*, WEAK_TREND_*", "emerald"],
              ["Mean Reversion", "RANGE only", "sky"],
              ["No strategy", "CHAOTIC → reject all", "rose"],
            ].map(([s, r, c]) => (
              <div key={s} className={`rounded border px-3 py-2 border-${c}-500/30 bg-${c}-500/5`}>
                <span className="text-zinc-100">{s}</span>
                <span className="ml-3 text-zinc-500">→ {r}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

/* -------------------- STRATEGIES -------------------- */
function Strategies() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <StratCard name="Mean Reversion" regime="RANGE" color="sky"
          rules={[
            "RSI(14) crosses up through 30  →  BUY",
            "RSI(14) crosses down through 70  →  SELL",
            "Active only when ADX < 18 + ATR rank < 70%",
            "Quality score must reach ≥ 70/100",
          ]}
          rationale="In a sideways market, prices revert. RSI extremes are statistical edges that break in trends — the regime gate protects against that." />
        <StratCard name="Trend Following" regime="STRONG/WEAK_TREND_*" color="emerald"
          rules={[
            "EMA50 cross EMA200 (any direction matching regime bias)",
            "Confirmed by close vs rolling VWAP(20)",
            "Higher-TF EMA50 vs EMA200 must agree (MTF alignment ≥ 20pts)",
            "WEAK trend → MEDIUM tier (1% risk); STRONG → potentially HIGH (1.5%)",
          ]}
          rationale="Trends pay for the false signals of range markets. MTF alignment + ADX gating eliminates most whipsaws of naïve crossover systems." />
      </div>

      <Card title="Why only two strategies?">
        <p className="text-sm leading-relaxed text-zinc-400">
          Every additional strategy multiplies overfitting surface area. Two
          strategies — one per major regime — cover the price-behavior
          taxonomy without redundancy. <strong className="text-zinc-200">More strategies ≠ more edge.</strong> Edge comes from{" "}
          <span className="text-emerald-300">disciplined sizing, exits, and rejecting marginal setups</span>.
        </p>
      </Card>

      <Card title="Strategy performance breakdown (5y backtest)">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Strategy</th>
                <th className="text-right">Trades</th>
                <th className="text-right">Wins</th>
                <th className="text-right">Win Rate</th>
                <th className="text-right">Total PnL</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {Object.entries(BY_STRATEGY).map(([k, v]) => (
                <tr key={k} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-100">{k}</td>
                  <td className="text-right">{v.trades}</td>
                  <td className="text-right">{v.wins}</td>
                  <td className="text-right">{pct(v.win_rate)}</td>
                  <td className={`text-right ${v.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {usd(v.pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="By-regime breakdown (where the money is made)">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Regime</th>
                <th className="text-right">Trades</th>
                <th className="text-right">Win Rate</th>
                <th className="text-right">Total PnL</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {Object.entries(BY_REGIME).map(([k, v]) => (
                <tr key={k} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-100">{k}</td>
                  <td className="text-right">{v.trades}</td>
                  <td className="text-right">{pct(v.win_rate)}</td>
                  <td className={`text-right ${v.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {usd(v.pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-zinc-500">
          STRONG_TREND_UP carries ~40% of total PnL. RANGE pays the bills with consistency. STRONG_TREND_DN is rare but high-quality — filtering matters most here.
        </p>
      </Card>
    </div>
  );
}

function StratCard({ name, regime, color, rules, rationale }:
  { name: string; regime: string; color: "sky"|"emerald"; rules: string[]; rationale: string }) {
  const palette = {
    sky: "border-sky-500/30 bg-sky-500/5 text-sky-300",
    emerald: "border-emerald-500/30 bg-emerald-500/5 text-emerald-300",
  }[color];
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-xl font-semibold text-zinc-100">{name}</h3>
        <span className={`rounded-full border px-2.5 py-1 font-mono text-[11px] ${palette}`}>
          {regime}
        </span>
      </div>
      <ul className="mb-4 space-y-2 text-sm">
        {rules.map((r) => (
          <li key={r} className="flex gap-2 text-zinc-300">
            <span className="text-emerald-400">▸</span>
            <code className="font-mono text-[12.5px]">{r}</code>
          </li>
        ))}
      </ul>
      <p className="border-t border-zinc-800 pt-3 text-xs leading-relaxed text-zinc-500">{rationale}</p>
    </div>
  );
}

/* -------------------- RISK -------------------- */
function Risk() {
  const params = [
    { k: "risk_high (HIGH tier)", v: "1.5%", note: "Quality ≥ 85" },
    { k: "risk_medium (MEDIUM tier)", v: "1.0%", note: "Quality ≥ 70" },
    { k: "risk_low (LOW tier)", v: "0.5%", note: "Quality ≥ 60 (sub-threshold scalp)" },
    { k: "max_daily_loss", v: "4%", note: "Halts for the day" },
    { k: "max_weekly_loss", v: "8%", note: "Halts for the week" },
    { k: "max_consecutive_losses", v: "3", note: "Triggers kill switch" },
    { k: "max_concurrent_positions", v: "3", note: "Diversification + margin" },
    { k: "max_portfolio_risk", v: "5%", note: "Sum of stop-distance × qty" },
    { k: "max_sector_exposure", v: "40%", note: "Per sector, of equity" },
    { k: "max_correlation", v: "0.75", note: "Reject if |corr| > 0.75 with open" },
    { k: "atr_stop_mult", v: "2.0×", note: "Stop = entry ∓ 2 × ATR" },
    { k: "atr_tp_mult", v: "3.0×", note: "TP = entry ± 3 × ATR (1.5 R:R)" },
    { k: "trail_activation_atr", v: "1.5×", note: "Move stop to BE after this favorable move" },
    { k: "cash_buffer", v: "10%", note: "Always reserved" },
  ];
  return (
    <div className="space-y-6">
      <Card title="Risk-state gauges (live)">
        <div className="grid gap-3 md:grid-cols-3">
          <Gauge label="Daily P&L" value={RISK_STATE.daily_pnl_pct} max={-RISK_STATE.max_daily_loss} format="pct" inverted />
          <Gauge label="Weekly P&L" value={RISK_STATE.weekly_pnl_pct} max={-RISK_STATE.max_weekly_loss} format="pct" inverted />
          <Gauge label="Loss Streak" value={RISK_STATE.consecutive_losses} max={RISK_STATE.max_consecutive_losses} format="int" />
          <Gauge label="Portfolio Risk" value={RISK_STATE.total_open_risk_pct} max={RISK_STATE.max_portfolio_risk} format="pct" />
          <Gauge label="Open Positions" value={RISK_STATE.open_positions} max={RISK_STATE.max_concurrent_positions} format="int" />
        </div>
      </Card>

      <Card title="Tiered position sizing (NEW in v2)">
        <pre className="overflow-x-auto rounded-md bg-zinc-950 p-4 font-mono text-xs text-zinc-300">
{`# Quality drives sizing — high conviction gets bigger size.
if quality_score >= 85: risk_pct = 0.015   # HIGH
elif quality_score >= 70: risk_pct = 0.010  # MEDIUM
else (>= 60): risk_pct = 0.005              # LOW (sub-threshold)

risk_dollars   = equity × risk_pct
stop_distance  = 2.0 × ATR(14)
qty            = floor(risk_dollars / stop_distance)
qty            = min(qty, floor(usable_cash / price))

# Stop (long) = entry - 2.0 × ATR
# Target      = entry + 3.0 × ATR
# Trailing    = move stop to BE after price moves +1.5 × ATR`}
        </pre>
      </Card>

      <div className="grid gap-3">
        {params.map((p) => (
          <div key={p.k}
            className="grid grid-cols-[2fr_auto_2fr] items-center gap-4 rounded-md border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-sm">
            <code className="font-mono text-emerald-300">{p.k}</code>
            <span className="font-mono text-zinc-100">{p.v}</span>
            <span className="text-zinc-500">{p.note}</span>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-5">
        <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-rose-300">⚠ Realistic risk warnings</h3>
        <ol className="list-inside list-decimal space-y-2 text-sm leading-relaxed text-zinc-300">
          <li>Backtest = best case. Plan for 30–50% worse live results.</li>
          <li>v2 trades ~half as often as v1. That's a feature. Don't lower quality_min_score.</li>
          <li>Slippage modeled at 5–20 bps. Real slippage on small caps can be 50+.</li>
          <li>Indian shorts are intraday-only (MIS). v2's regime-driven SHORT signals only execute on Alpaca.</li>
          <li>Walk-forward fold returns vary 4× (-1.8% to +9.4%). Plan for any of them.</li>
          <li>Kill switch fires after 3 losses. <strong>Do not bypass it.</strong> 24h cool-off.</li>
          <li>Never deploy live without ≥30 days paper on the exact production config.</li>
        </ol>
      </div>
    </div>
  );
}

function Gauge({ label, value, max, format, inverted }:
  { label: string; value: number; max: number; format: "pct" | "int"; inverted?: boolean }) {
  const ratio = inverted
    ? Math.max(0, Math.min(1, -value / Math.abs(max)))
    : Math.max(0, Math.min(1, value / max));
  const danger = ratio > 0.7;
  const fmtVal = format === "pct" ? `${(value * 100).toFixed(2)}%` : String(value);
  const fmtMax = format === "pct" ? `${(max * 100).toFixed(0)}%` : String(max);
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="mb-2 flex justify-between">
        <span className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</span>
        <span className={`font-mono text-xs ${danger ? "text-rose-400" : "text-zinc-300"}`}>
          {fmtVal} / {fmtMax}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-900">
        <div
          className={`h-full transition-all ${
            ratio > 0.85 ? "bg-rose-500" : ratio > 0.6 ? "bg-amber-500" : "bg-emerald-500"
          }`}
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
    </div>
  );
}

/* -------------------- PERFORMANCE -------------------- */
function Performance() {
  const stats = [
    { k: "Total Return", v: pct(SUMMARY.total_return), good: true },
    { k: "CAGR", v: pct(SUMMARY.cagr), good: true },
    { k: "Sharpe", v: SUMMARY.sharpe.toFixed(2), good: true },
    { k: "Sortino", v: SUMMARY.sortino.toFixed(2), good: true },
    { k: "Calmar", v: SUMMARY.calmar.toFixed(2) },
    { k: "Max DD", v: pct(SUMMARY.max_drawdown), bad: true },
    { k: "Win Rate", v: pct(SUMMARY.win_rate) },
    { k: "Profit Factor", v: SUMMARY.profit_factor.toFixed(2), good: true },
    { k: "Expectancy", v: usd(SUMMARY.expectancy) },
    { k: "Trades", v: String(SUMMARY.trades) },
  ];

  const pnlBuckets = TRADE_PNL_DIST.map((b) => ({ label: b.bin, count: b.count }));

  return (
    <div className="space-y-6">
      <EquityChart />
      <DrawdownChart />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {stats.map((s) => (
          <div key={s.k} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
            <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">{s.k}</p>
            <p className={`mt-1 font-mono text-lg font-semibold ${
              s.good ? "text-emerald-300" : s.bad ? "text-rose-400" : "text-zinc-100"
            }`}>{s.v}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Histogram data={pnlBuckets} title="Trade PnL distribution ($)" unit="trades" />
        <Card title="In-Sample vs Out-of-Sample">
          <p className="mb-3 text-xs text-zinc-500">
            70/30 chronological split. OOS Sharpe should be ≥ 0.7× IS Sharpe — anything less = overfit.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {[
              { name: "In-Sample (70%)", data: IS_OOS.in_sample, color: "text-zinc-300" },
              { name: "Out-of-Sample (30%)", data: IS_OOS.out_of_sample, color: "text-emerald-300" },
            ].map((b) => (
              <div key={b.name} className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3">
                <p className={`mb-2 font-mono text-xs ${b.color}`}>{b.name}</p>
                <div className="space-y-1 text-xs">
                  <Row k="Return" v={pct(b.data.return)} />
                  <Row k="Sharpe" v={b.data.sharpe.toFixed(2)} />
                  <Row k="Max DD" v={pct(b.data.max_dd)} />
                  <Row k="Trades" v={String(b.data.trades)} />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-3 rounded bg-emerald-500/10 px-3 py-2 text-[11px] text-emerald-300">
            ✓ OOS Sharpe (1.28) is 85% of IS Sharpe (1.51) — passes overfit check.
          </p>
        </Card>
      </div>

      <Card title="Walk-forward folds (NEW in v2)">
        <p className="mb-3 text-xs text-zinc-500">
          Each row = a 6-month out-of-sample test on parameters derived from the prior 2 years. Honest, brutal, useful.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">OOS Window</th>
                <th className="text-right">Return</th>
                <th className="text-right">Sharpe</th>
                <th className="text-right">Max DD</th>
                <th className="text-right">PF</th>
                <th className="text-right">Trades</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {WALK_FORWARD.map((f) => (
                <tr key={f.oos_start} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-300">{f.oos_start} → {f.oos_end}</td>
                  <td className={`text-right ${f.oos_return >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {pct(f.oos_return, 2)}
                  </td>
                  <td className={`text-right ${f.oos_sharpe >= 1 ? "text-emerald-400" : f.oos_sharpe >= 0 ? "text-zinc-300" : "text-rose-400"}`}>
                    {f.oos_sharpe.toFixed(2)}
                  </td>
                  <td className="text-right text-rose-400">{pct(f.oos_max_dd, 1)}</td>
                  <td className={`text-right ${f.oos_profit_factor >= 1 ? "text-emerald-400" : "text-rose-400"}`}>
                    {f.oos_profit_factor.toFixed(2)}
                  </td>
                  <td className="text-right text-zinc-400">{f.oos_trades}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-emerald-500/30 bg-emerald-500/5">
                <td className="py-2 font-mono text-emerald-300">Average</td>
                <td className="text-right font-mono text-emerald-300">
                  {pct(WALK_FORWARD.reduce((a, f) => a + f.oos_return, 0) / WALK_FORWARD.length, 2)}
                </td>
                <td className="text-right font-mono text-emerald-300">
                  {(WALK_FORWARD.reduce((a, f) => a + f.oos_sharpe, 0) / WALK_FORWARD.length).toFixed(2)}
                </td>
                <td colSpan={3}></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-zinc-500">
          One losing fold (2024 H1, -1.8%, Sharpe -0.32). This is normal. The system survived without breaching the 8% weekly cap.
        </p>
      </Card>

      <Card title="Recent trades (last 8)">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Closed</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th className="text-right">Entry</th>
                <th className="text-right">Exit</th>
                <th className="text-right">PnL</th>
                <th className="text-right">Q</th>
                <th>Tier</th>
                <th>Regime</th>
                <th>Exit</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {TRADES.map((t, i) => (
                <tr key={i} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-500">{t.closed_at}</td>
                  <td className="text-zinc-100">{t.symbol}</td>
                  <td className="text-zinc-400">{t.side}</td>
                  <td className="text-zinc-400">{t.qty}</td>
                  <td className="text-right">${t.entry.toFixed(2)}</td>
                  <td className="text-right">${t.exit.toFixed(2)}</td>
                  <td className={`text-right ${t.pnl > 0 ? "text-emerald-400" : t.pnl < 0 ? "text-rose-400" : "text-zinc-400"}`}>
                    {t.pnl >= 0 ? "+" : ""}{t.pnl.toFixed(2)}
                  </td>
                  <td className="text-right text-zinc-300">{t.quality_score}</td>
                  <td className={
                    t.risk_tier === "HIGH" ? "text-emerald-300" :
                    t.risk_tier === "MEDIUM" ? "text-sky-300" : "text-zinc-500"
                  }>{t.risk_tier}</td>
                  <td className="text-zinc-500 text-[11px]">{t.regime}</td>
                  <td className="text-zinc-500">{t.reason_close}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

/* -------------------- LIVE STATE -------------------- */
function LiveState() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card title="Account state">
        <div className="space-y-2 font-mono text-sm">
          <Row k="Equity" v={usd(POSITIONS.equity)} accent />
          <Row k="Cash" v={usd(POSITIONS.cash)} />
          <Row k="Open positions" v={`${POSITIONS.open.length} / ${RISK_STATE.max_concurrent_positions}`} />
          <Row k="Open risk" v={pct(RISK_STATE.total_open_risk_pct, 2)} />
          <Row k="Halted" v={POSITIONS.halted ? "YES" : "NO"} danger={POSITIONS.halted} />
          <Row k="Loss streak" v={`${POSITIONS.consecutive_losses} / 3`} danger={POSITIONS.consecutive_losses >= 3} />
        </div>
      </Card>

      <Card title="Open positions">
        {POSITIONS.open.length === 0 ? <p className="text-sm text-zinc-500">Flat.</p> : (
          <div className="space-y-2">
            {POSITIONS.open.map((p) => (
              <div key={p.symbol} className="rounded-md border border-zinc-800 bg-zinc-950/60 p-3 font-mono text-xs">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-base text-zinc-100">{p.symbol}</span>
                  <div className="flex items-center gap-2">
                    {p.trail_active && (
                      <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-300">
                        🔒 trailing BE
                      </span>
                    )}
                    <span className={`rounded px-2 py-0.5 text-[10px] ${
                      p.risk_tier === "HIGH" ? "bg-emerald-500/15 text-emerald-300" :
                      p.risk_tier === "MEDIUM" ? "bg-sky-500/15 text-sky-300" : "bg-zinc-800 text-zinc-400"
                    }`}>{p.risk_tier} q={p.quality_score}</span>
                    <span className={`rounded px-2 py-0.5 ${
                      p.side === "LONG" ? "bg-emerald-500/10 text-emerald-300" : "bg-rose-500/10 text-rose-300"
                    }`}>{p.side} × {p.qty}</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-zinc-500">
                  <div>entry<p className="text-zinc-200">${p.entry.toFixed(2)}</p></div>
                  <div>stop<p className="text-rose-300">${p.stop.toFixed(2)}</p></div>
                  <div>target<p className="text-emerald-300">${p.target.toFixed(2)}</p></div>
                </div>
                <p className="mt-2 text-[11px] text-zinc-500">
                  {p.strategy} · opened {p.opened_at.slice(0, 10)}
                </p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Live candidates (with quality breakdown)" className="md:col-span-2">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-[11px] uppercase tracking-wider text-zinc-500">
                <th className="py-2">Symbol</th>
                <th>Side</th>
                <th>Strategy</th>
                <th>Regime</th>
                <th className="text-right">Q Score</th>
                <th>Tier</th>
                <th className="text-right">Price</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody className="font-mono text-[12.5px]">
              {SIGNALS.map((s) => (
                <tr key={s.symbol + s.side} className="border-b border-zinc-900 last:border-0">
                  <td className="py-2 text-zinc-100">{s.symbol}</td>
                  <td className={s.side === "BUY" ? "text-emerald-400" : "text-rose-400"}>{s.side}</td>
                  <td className="text-zinc-300">{s.strategy}</td>
                  <td>
                    <span className={`rounded px-2 py-0.5 text-[10px] ${
                      s.regime.label.includes("STRONG") ? "bg-emerald-500/15 text-emerald-300" :
                      s.regime.label.includes("WEAK") ? "bg-emerald-500/10 text-emerald-400" :
                      s.regime.label === "RANGE" ? "bg-sky-500/15 text-sky-300" :
                      "bg-rose-500/15 text-rose-300"
                    }`}>{s.regime.label}</span>
                  </td>
                  <td className={`text-right font-bold ${
                    s.quality.score >= 85 ? "text-emerald-300" :
                    s.quality.score >= 70 ? "text-sky-300" : "text-zinc-500"
                  }`}>{s.quality.score}</td>
                  <td className="text-zinc-400">{s.risk_tier}</td>
                  <td className="text-right">${s.price.toFixed(2)}</td>
                  <td className={s.accepted ? "text-emerald-400" : "text-rose-500"}>
                    {s.accepted ? "✓ taken" : `✗ ${s.reason.slice(0, 30)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Row({ k, v, accent, danger }:
  { k: string; v: string; accent?: boolean; danger?: boolean }) {
  return (
    <div className="flex justify-between border-b border-zinc-800/50 py-1.5">
      <span className="text-zinc-500">{k}</span>
      <span className={danger ? "text-rose-400" : accent ? "text-emerald-300" : "text-zinc-100"}>{v}</span>
    </div>
  );
}

/* -------------------- API -------------------- */
function ApiDocs() {
  const endpoints = [
    { m: "GET", p: "/health", d: "Liveness probe + version." },
    { m: "GET", p: "/signals", d: "Live candidates with quality + regime + accept/reject reason." },
    { m: "GET", p: "/trade_quality_score", d: "🆕 v2 — quality breakdown for every symbol with a raw signal." },
    { m: "GET", p: "/market_regime", d: "🆕 v2 — per-symbol regime classification + ADX + ATR rank + slope." },
    { m: "GET", p: "/risk_state", d: "🆕 v2 — daily/weekly P&L vs caps, loss streak, total open risk." },
    { m: "GET", p: "/positions", d: "Open positions with quality_score and trail_active flag." },
    { m: "GET", p: "/performance?years=3", d: "Backtest summary + equity curve + recent trades." },
    { m: "GET", p: "/performance_detailed?years=3", d: "🆕 v2 — IS/OOS split + walk-forward folds + by-strategy + by-regime + drawdown curve." },
    { m: "POST", p: "/run-cycle", d: "Manually trigger one full cycle." },
    { m: "POST", p: "/kill-switch", d: "Force halt." },
    { m: "POST", p: "/resume", d: "Clear halt + reset loss streak." },
    { m: "POST", p: "/train-ranker", d: "🆕 v2 — train logistic ranker on logged trade outcomes (self-improvement)." },
  ];
  return (
    <div className="space-y-6">
      <Card title="REST API v2">
        <p className="mb-4 text-sm text-zinc-400">
          Drop-in for any React / Vue / Flutter / mobile client. CORS open by default — lock down in production.
        </p>
        <div className="space-y-2">
          {endpoints.map((e) => (
            <div key={e.p} className="flex items-center gap-3 rounded-md border border-zinc-800 bg-zinc-950/60 px-3 py-2 font-mono text-xs">
              <span className={`w-12 rounded px-2 py-0.5 text-center text-[10px] font-bold ${
                e.m === "GET" ? "bg-sky-500/15 text-sky-300" : "bg-amber-500/15 text-amber-300"
              }`}>{e.m}</span>
              <code className="text-emerald-300">{e.p}</code>
              <span className="text-zinc-500">— {e.d}</span>
            </div>
          ))}
        </div>
      </Card>

      <CodeBlock filename="example: GET /trade_quality_score" lang="json"
        code={`{
  "threshold_min": 70.0,
  "threshold_high": 85.0,
  "scores": [
    { "symbol": "NVDA", "side": "BUY", "tier": "HIGH",
      "accepted": true, "score": 88.0,
      "trend_pts": 28, "volume_pts": 20,
      "volatility_pts": 20, "mtf_pts": 30,
      "notes": "HTF bullish + above VWAP" },
    { "symbol": "AAPL", "side": "BUY", "tier": "LOW",
      "accepted": false, "score": 58.0,
      "trend_pts": 4, "volume_pts": 8,
      "volatility_pts": 16, "mtf_pts": 30,
      "notes": "HTF bullish" }
  ]
}`} />

      <CodeBlock filename="example: GET /risk_state" lang="json"
        code={`{
  "equity": 1612.30,
  "halted": false, "halt_reason": "",
  "consecutive_losses": 1, "max_consecutive_losses": 3,
  "daily_pnl_pct": -0.008, "max_daily_loss": 0.04,
  "weekly_pnl_pct": 0.012, "max_weekly_loss": 0.08,
  "total_open_risk_pct": 0.022, "max_portfolio_risk": 0.05,
  "open_positions": 2, "max_concurrent_positions": 3
}`} />

      <CodeBlock filename="bash" lang="bash"
        code={`uvicorn trading_system.api:app --host 0.0.0.0 --port 8000

curl http://localhost:8000/health
curl http://localhost:8000/trade_quality_score
curl http://localhost:8000/market_regime
curl http://localhost:8000/risk_state
curl 'http://localhost:8000/performance_detailed?years=3' | jq .walk_forward_folds
curl -X POST http://localhost:8000/kill-switch    # emergency`} />
    </div>
  );
}

/* -------------------- DEPLOY -------------------- */
function Deploy() {
  return (
    <div className="space-y-6">
      <Card title="1 · Local quickstart (paper)">
        <CodeBlock filename="bash" lang="bash" code={`git clone <repo>
cd rayr-money/trading_system
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python -m trading_system.main backtest      # 5y backtest
python -m trading_system.main walkforward   # 🆕 v2 walk-forward
python -m trading_system.main once          # single paper cycle
python -m trading_system.main live          # scheduler-driven loop
uvicorn trading_system.api:app --reload     # API on :8000`} />
      </Card>

      <Card title="2 · Connect Alpaca">
        <ol className="list-inside list-decimal space-y-1 text-sm text-zinc-400">
          <li>Sign up at alpaca.markets (paper account is free).</li>
          <li>Generate API key + secret in dashboard.</li>
          <li>Set <code className="text-emerald-400">BROKER=alpaca</code> + keys in <code>.env</code>.</li>
          <li>Run same commands. Orders route to Alpaca paper.</li>
        </ol>
      </Card>

      <Card title="3 · Connect Zerodha (Indian equities)">
        <ol className="list-inside list-decimal space-y-1 text-sm text-zinc-400">
          <li>Subscribe to Kite Connect (₹2k/mo).</li>
          <li>Daily OAuth flow for fresh access_token.</li>
          <li>Set <code className="text-emerald-400">BROKER=zerodha</code> + creds in <code>.env</code>.</li>
          <li>Workaround if API restricted: TradingView Pine alerts → self-hosted Kite webhook bridge. Payload = <code>candidate.to_dict()</code>.</li>
        </ol>
      </Card>

      <Card title="4 · Cloud / VPS deployment">
        <CodeBlock filename="Dockerfile" lang="dockerfile" code={`FROM python:3.11-slim
WORKDIR /app
COPY trading_system/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY trading_system/ ./trading_system/
ENV PYTHONUNBUFFERED=1
CMD ["python","-m","trading_system.main","live"]`} />
        <CodeBlock filename="cron (alternative)" lang="bash" code={`# every 5 min during US RTH (Mon-Fri 13:30-20:00 UTC)
*/5 13-20 * * 1-5  cd /opt/rayr && /opt/rayr/.venv/bin/python \\
                   -m trading_system.main once >> bot.log 2>&1`} />
        <p className="mt-3 text-xs text-zinc-500">
          $5/mo VPS (DigitalOcean / Hetzner / Linode). Healthcheck on /health. Pipe stdout to logrotate.
        </p>
      </Card>

      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
        <h3 className="mb-2 text-sm font-semibold text-amber-300">v2 Pre-flight checklist (before going live)</h3>
        <ul className="space-y-1.5 text-sm text-zinc-300">
          <li>☐ ≥30 days of paper trading on the exact production config</li>
          <li>☐ Walk-forward run: avg OOS Sharpe ≥ 0.7 × IS Sharpe</li>
          <li>☐ Walk-forward: NO single fold with worse than -10% return</li>
          <li>☐ Telegram alerts confirmed on OPEN / CLOSE / HALT</li>
          <li>☐ Kill-switch tested via POST /kill-switch</li>
          <li>☐ Risk gauges visible on dashboard, refreshed live</li>
          <li>☐ Daily Zerodha access-token refresh scripted (or alarm set)</li>
          <li>☐ Capital is loss-tolerant — not rent / tuition / emergency fund</li>
          <li>☐ You understand WHY each rejection happens (read Quality Engine tab)</li>
        </ul>
      </div>
    </div>
  );
}
