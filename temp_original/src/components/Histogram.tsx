type Item = { label: string; count: number; highlight?: boolean };

export default function Histogram({
  data,
  title,
  threshold,
  unit = "trades",
}: {
  data: Item[];
  title: string;
  threshold?: { at: number; label: string };
  unit?: string;
}) {
  const max = Math.max(...data.map((d) => d.count));
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
        {threshold && (
          <span className="font-mono text-[11px] text-emerald-400">
            ▸ {threshold.label}
          </span>
        )}
      </div>
      <div className="space-y-1.5">
        {data.map((d, i) => {
          const w = (d.count / max) * 100;
          const past = threshold ? i >= threshold.at : false;
          return (
            <div key={d.label} className="flex items-center gap-2">
              <span className="w-16 text-right font-mono text-[11px] text-zinc-500">
                {d.label}
              </span>
              <div className="relative h-5 flex-1 rounded bg-zinc-900">
                <div
                  className={`h-full rounded transition-all ${
                    past
                      ? "bg-gradient-to-r from-emerald-500/70 to-emerald-400"
                      : "bg-zinc-700"
                  }`}
                  style={{ width: `${w}%` }}
                />
                <span className="absolute inset-y-0 right-2 flex items-center font-mono text-[10px] text-zinc-300">
                  {d.count}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[10px] text-zinc-500">
        x-axis: count of {unit}
      </p>
    </div>
  );
}
