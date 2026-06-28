interface MetricBarProps {
  label: string;
  value: number;
}

function MetricBar({ label, value }: MetricBarProps) {
  const pct = Math.round(value * 100);
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-zinc-300 font-semibold">{label}</span>
        <span className="text-white font-black">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-zinc-800">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

interface ModelMetricsProps {
  auc: number;
  precision: number;
  recall: number;
  f1: number;
}

export default function ModelMetrics({ auc, precision, recall, f1 }: ModelMetricsProps) {
  return (
    <div className="rounded-xl bg-zinc-900 p-6">
      <h2 className="text-xs font-black uppercase tracking-widest text-zinc-500 mb-4">
        Model Performance
      </h2>
      <MetricBar label="AUC-ROC" value={auc} />
      <MetricBar label="Precision" value={precision} />
      <MetricBar label="Recall" value={recall} />
      <MetricBar label="F1 Score" value={f1} />
    </div>
  );
}
