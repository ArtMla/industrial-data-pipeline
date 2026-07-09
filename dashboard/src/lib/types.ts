export interface PredictionRow {
  id: number;
  timestamp: string;
  air_temp: number;
  process_temp: number;
  rotational_speed: number;
  torque: number;
  tool_wear: number;
  product_type: string;
  failure_prob: number;
  predicted_failure: boolean;
  failure_modes: Record<string, number>;
  model_version: string;
}

export interface ModelMetricsData {
  auc: number;
  precision: number;
  recall: number;
  f1: number;
  total_predictions: number;
  failure_rate_30d: number;
  model_version: string;
}

export interface HealthData {
  status: string;
  model_version: string;
  db: string;
}
