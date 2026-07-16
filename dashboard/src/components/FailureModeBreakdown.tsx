const FAILURE_MODE_INFO: { code: string; label: string }[] = [
  { code: "TWF", label: "Tool Wear Failure" },
  { code: "HDF", label: "Heat Dissipation Failure" },
  { code: "PWF", label: "Power Failure" },
  { code: "OSF", label: "Overstrain Failure" },
  { code: "RNF", label: "Random Failure" },
];

// Failure modes are rare events (few % even at their riskiest), so the bands
// sit well below the 50% threshold used for the overall machine_failure call.
function severity(prob: number): "good" | "warning" | "critical" {
  if (prob >= 0.3) return "critical";
  if (prob >= 0.1) return "warning";
  return "good";
}

const SEVERITY_STYLES = {
  good: { fill: "bg-green-500", track: "bg-green-500/15", text: "text-green-400" },
  warning: { fill: "bg-amber-500", track: "bg-amber-500/15", text: "text-amber-400" },
  critical: { fill: "bg-red-500", track: "bg-red-500/15", text: "text-red-400" },
};

interface FailureModeBreakdownProps {
  failureModes: Record<string, number>;
}

export default function FailureModeBreakdown({ failureModes }: FailureModeBreakdownProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 px-3 py-4">
      {FAILURE_MODE_INFO.map(({ code, label }) => {
        const prob = Math.max(0, Math.min(1, failureModes[code] ?? 0));
        const pct = prob * 100;
        const style = SEVERITY_STYLES[severity(prob)];
        return (
          <div key={code} title={`${label}: ${pct.toFixed(1)}%`}>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">
                {code}
              </span>
              <span className={`text-xs font-mono font-bold ${style.text}`}>
                {pct.toFixed(1)}%
              </span>
            </div>
            <div className={`h-1.5 rounded-full ${style.track}`}>
              <div
                className={`h-full rounded-full ${style.fill}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-[10px] text-zinc-600 mt-1">{label}</p>
          </div>
        );
      })}
    </div>
  );
}
