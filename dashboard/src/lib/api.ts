import type { HealthData, ModelMetricsData, PredictionRow } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, revalidate = 30): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate },
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export const fetchMetrics = () => apiFetch<ModelMetricsData>("/metrics", 60);
export const fetchHealth = () => apiFetch<HealthData>("/health", 10);

interface SensorReading {
  air_temp: number;
  process_temp: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
  product_type?: string;
}

interface PredictionResponse {
  prediction_id: number;
  failure_probability: number;
  predicted_failure: boolean;
  failure_modes: Record<string, number>;
  model_version: string;
}

export async function postPredict(reading: SensorReading): Promise<PredictionRow> {
  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reading),
  });
  if (!res.ok) throw new Error(`Predict API ${res.status}`);
  const data: PredictionResponse = await res.json();

  // /predict only echoes back the prediction outcome, not the input reading —
  // stitch the two together so the table has a stable id and the sensor values to show.
  return {
    id: data.prediction_id,
    timestamp: new Date().toISOString(),
    product_type: "M",
    ...reading,
    failure_prob: data.failure_probability,
    predicted_failure: data.predicted_failure,
    failure_modes: data.failure_modes,
    model_version: data.model_version,
  };
}
