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

export async function postPredict(reading: {
  air_temp: number;
  process_temp: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
  product_type?: string;
}): Promise<PredictionRow> {
  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reading),
  });
  if (!res.ok) throw new Error(`Predict API ${res.status}`);
  return res.json();
}
