import { useMemo } from "react";
import { EQUITY_CURVE } from "../data/mockData";

export default function EquityChart() {
  const { path, areaPath, peaks, ddPath, minY, maxY, ticks } = useMemo(() => {
    const data = EQUITY_CURVE;
    const w = 1000;
    const h = 280;
    const pad = { l: 50, r: 12, t: 12, b: 28 };
    const xs = data.map((_, i) => i);
    const ys = data.map((d) => d.equity);
    const minY = Math.min(...ys) * 0.98;
    const maxY = Math.max(...ys) * 1.02;
    const sx = (i: number) =>
      pad.l + (i / (xs.length - 1)) * (w - pad.l - pad.r);
    const sy = (v: number) =>
      pad.t + (1 - (v - minY) / (maxY - minY)) * (h - pad.t - pad.b);

    let path = "";
    data.forEach((d, i) => {
      path += `${i === 0 ? "M" : "L"}${sx(i)},${sy(d.equity)} `;
    });
    const areaPath =
      path +
      `L${sx(xs.length - 1)},${h - pad.b} L${sx(0)},${h - pad.b} Z`;

    // Drawdown trail (running max)
    let runMax = -Infinity;
    const ddPoints = data.map((d) => {
      runMax = Math.max(runMax, d.equity);
      return d.equity / runMax - 1;
    });
    const ddMin = Math.min(...ddPoints);
    const ddH = 60;
    const ddSy = (v: number) =>
      h - pad.b - 4 - ((v / ddMin) * ddH);
    let ddPath = "";
    ddPoints.forEach((v, i) => {
      ddPath += `${i === 0 ? "M" : "L"}${sx(i)},${ddSy(v)} `;
    });

    const peaks = [
      { i: 0, v: data[0].equity, label: data[0].ts },
      {
        i: data.length - 1,
        v: data[data.length - 1].equity,
        label: data[data.length - 1].ts,
      },
    ];

    const ticks = 5;
    return { path, areaPath, peaks, ddPath, minY, maxY, ticks };
  }, []);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Equity Curve · 5y backtest
          </p>
          <p className="font-mono text-lg text-emerald-400">
            $1,000 → $1,738.42
            <span className="ml-2 text-sm text-zinc-500">+73.8%</span>
          </p>
        </div>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" /> Equity
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500/70" /> Drawdown
          </span>
        </div>
      </div>
      <svg viewBox="0 0 1000 280" className="h-auto w-full">
        <defs>
          <linearGradient id="eqGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Y grid */}
        {Array.from({ length: ticks }).map((_, i) => {
          const y = 12 + (i / (ticks - 1)) * (280 - 12 - 28);
          const v = maxY - (i / (ticks - 1)) * (maxY - minY);
          return (
            <g key={i}>
              <line
                x1={50}
                x2={988}
                y1={y}
                y2={y}
                stroke="#27272a"
                strokeDasharray="2 4"
              />
              <text x={8} y={y + 3} fontSize="10" fill="#71717a">
                ${v.toFixed(0)}
              </text>
            </g>
          );
        })}
        <path d={areaPath} fill="url(#eqGrad)" />
        <path d={path} fill="none" stroke="#10b981" strokeWidth="1.6" />
        <path
          d={ddPath}
          fill="none"
          stroke="#fb7185"
          strokeWidth="1.2"
          opacity="0.7"
        />
        {peaks.map((p) => (
          <text
            key={p.i}
            x={p.i === 0 ? 56 : 940}
            y={272}
            fontSize="10"
            fill="#71717a"
          >
            {p.label}
          </text>
        ))}
      </svg>
    </div>
  );
}
