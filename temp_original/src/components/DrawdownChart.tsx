import { DRAWDOWN_CURVE } from "../data/mockData";

export default function DrawdownChart() {
  const data = DRAWDOWN_CURVE;
  const w = 1000, h = 200;
  const pad = { l: 50, r: 12, t: 12, b: 24 };
  const minDD = Math.min(...data.map((d) => d.dd));
  const sx = (i: number) =>
    pad.l + (i / (data.length - 1)) * (w - pad.l - pad.r);
  const sy = (v: number) =>
    pad.t + ((v - 0) / (minDD - 0)) * (h - pad.t - pad.b);
  let path = "";
  data.forEach((d, i) => {
    path += `${i === 0 ? "M" : "L"}${sx(i)},${sy(d.dd)} `;
  });
  const area = path + `L${sx(data.length - 1)},${pad.t} L${sx(0)},${pad.t} Z`;
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-zinc-500">
            Drawdown Curve · 5y
          </p>
          <p className="font-mono text-lg text-rose-400">
            Max DD {(minDD * 100).toFixed(2)}%
          </p>
        </div>
        <span className="font-mono text-[11px] text-zinc-500">
          underwater equity (%)
        </span>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-auto w-full">
        <defs>
          <linearGradient id="ddGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#fb7185" stopOpacity="0" />
            <stop offset="100%" stopColor="#fb7185" stopOpacity="0.4" />
          </linearGradient>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((t, i) => {
          const y = pad.t + t * (h - pad.t - pad.b);
          const v = -t * Math.abs(minDD) * 100;
          return (
            <g key={i}>
              <line
                x1={pad.l}
                x2={w - pad.r}
                y1={y}
                y2={y}
                stroke="#27272a"
                strokeDasharray="2 4"
              />
              <text x={8} y={y + 3} fontSize="10" fill="#71717a">
                {v.toFixed(1)}%
              </text>
            </g>
          );
        })}
        <path d={area} fill="url(#ddGrad)" />
        <path d={path} fill="none" stroke="#fb7185" strokeWidth="1.4" />
      </svg>
    </div>
  );
}
