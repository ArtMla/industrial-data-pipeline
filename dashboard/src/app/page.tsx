import KpiCard from "@/components/KpiCard";
import FeatureChart from "@/components/FeatureChart";
import { fetchMetrics, fetchHealth } from "@/lib/api";

export const revalidate = 60;

export default async function HomePage() {
  let metrics = null;
  let health = null;

  try {
    [metrics, health] = await Promise.all([fetchMetrics(), fetchHealth()]);
  } catch {
    // API not reachable — show placeholder values
  }

  const failureRatePct = metrics
    ? `${(metrics.failure_rate_30d * 100).toFixed(1)}%`
    : "—";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white mb-1">
          Industrial Predictive Maintenance
        </h1>
        <p className="text-sm text-zinc-400">
          Real-time machine failure prediction · AI4I 2020 dataset · XGBoost AUC 0.96
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          label="Total Predictions"
          value={metrics?.total_predictions?.toLocaleString() ?? "—"}
          sub="all time"
          accent="blue"
        />
        <KpiCard
          label="Failure Rate (30d)"
          value={failureRatePct}
          sub="avg failure probability"
          accent={
            metrics && metrics.failure_rate_30d > 0.1 ? "red" : "green"
          }
        />
        <KpiCard
          label="Model AUC"
          value={metrics ? metrics.auc.toFixed(2) : "—"}
          sub="XGBoost · test set"
          accent="blue"
        />
        <KpiCard
          label="API Status"
          value={health?.status === "ok" ? "Online" : "Offline"}
          sub={health?.db ?? "checking…"}
          accent={health?.status === "ok" ? "green" : "red"}
        />
      </div>

      <FeatureChart />

      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
        <h2 className="text-xs font-black uppercase tracking-widest text-zinc-500 mb-3">
          About This Platform
        </h2>
        <p className="text-sm text-zinc-300 leading-relaxed">
          End-to-end Industrie 4.0 data pipeline: raw sensor CSV ingested to S3, schema-validated
          and converted to Parquet via AWS Glue, physics-informed features (temperature delta,
          mechanical power, wear rate) loaded into PostgreSQL, XGBoost classifier trained with
          MLflow tracking, and served via this FastAPI microservice with prediction audit logging.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          {["Python", "XGBoost", "AWS S3", "AWS Glue", "PostgreSQL", "FastAPI", "Docker", "Next.js", "GitHub Actions"].map((t) => (
            <span key={t} className="px-2 py-1 bg-zinc-800 text-zinc-300 text-xs rounded-full">
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
