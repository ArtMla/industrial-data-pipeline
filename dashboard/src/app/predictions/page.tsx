import PredictionTable from "@/components/PredictionTable";

export default function PredictionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white mb-1">Prediction Log</h1>
        <p className="text-sm text-zinc-400">
          Live predictions from the FastAPI inference endpoint with PostgreSQL audit trail.
        </p>
      </div>

      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4 text-xs text-zinc-400">
        <strong className="text-zinc-300">How it works:</strong> Each prediction is scored by the
        XGBoost model loaded from S3, then written to the PostgreSQL predictions table via asyncpg.
        Failure probability &gt; 50% triggers a FAILURE classification.
      </div>

      <PredictionTable />
    </div>
  );
}
