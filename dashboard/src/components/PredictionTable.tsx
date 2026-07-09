"use client";

import { useEffect, useState } from "react";
import { postPredict } from "@/lib/api";
import type { PredictionRow } from "@/lib/types";
import clsx from "clsx";

const SAMPLE_READINGS = [
  { air_temp: 298.1, process_temp: 308.6, rotational_speed: 1551, torque: 42.8, tool_wear: 0, product_type: "M" },
  { air_temp: 302.5, process_temp: 311.2, rotational_speed: 1425, torque: 63.5, tool_wear: 200, product_type: "H" },
  { air_temp: 299.3, process_temp: 309.1, rotational_speed: 1600, torque: 38.0, tool_wear: 120, product_type: "L" },
];

export default function PredictionTable() {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [loading, setLoading] = useState(false);

  const runSample = async () => {
    setLoading(true);
    try {
      const results = await Promise.all(SAMPLE_READINGS.map(postPredict));
      setRows((prev) => [...results.reverse(), ...prev].slice(0, 50));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-black uppercase tracking-widest text-zinc-500">
          Prediction Log
        </h2>
        <button
          onClick={runSample}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-colors"
        >
          {loading ? "Running…" : "Run Sample Predictions"}
        </button>
      </div>

      {rows.length === 0 ? (
        <p className="text-zinc-500 text-sm text-center py-12">
          Click &quot;Run Sample Predictions&quot; to see live results from the API.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500 text-xs uppercase tracking-wider">
                <th className="text-left p-3">ID</th>
                <th className="text-left p-3">Air Temp</th>
                <th className="text-left p-3">Torque</th>
                <th className="text-left p-3">Tool Wear</th>
                <th className="text-left p-3">Failure Prob</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Model</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-zinc-800 hover:bg-zinc-900/50">
                  <td className="p-3 text-zinc-400 font-mono">#{row.id}</td>
                  <td className="p-3 text-zinc-300">{row.air_temp?.toFixed(1) ?? "—"} K</td>
                  <td className="p-3 text-zinc-300">{row.torque?.toFixed(1) ?? "—"} Nm</td>
                  <td className="p-3 text-zinc-300">{row.tool_wear ?? "—"} min</td>
                  <td className="p-3">
                    <span
                      className={clsx(
                        "font-mono font-bold",
                        (row.failure_prob ?? row.failure_probability) > 0.5
                          ? "text-red-400"
                          : "text-green-400"
                      )}
                    >
                      {((row.failure_prob ?? row.failure_probability) * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td className="p-3">
                    <span
                      className={clsx(
                        "px-2 py-0.5 rounded-full text-xs font-bold",
                        (row.predicted_failure ?? row.predicted_failure)
                          ? "bg-red-900/50 text-red-300"
                          : "bg-green-900/50 text-green-300"
                      )}
                    >
                      {row.predicted_failure ? "FAILURE" : "OK"}
                    </span>
                  </td>
                  <td className="p-3 text-zinc-500 font-mono text-xs">
                    {(row.model_version ?? "").slice(0, 16)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
