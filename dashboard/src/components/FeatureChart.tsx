"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface DataPoint {
  index: number;
  temp_diff: number;
  mechanical_power: number;
}

const SAMPLE_DATA: DataPoint[] = Array.from({ length: 20 }, (_, i) => ({
  index: i + 1,
  temp_diff: 9.5 + Math.sin(i * 0.4) * 1.5 + Math.random() * 0.5,
  mechanical_power: 6200 + Math.cos(i * 0.3) * 400 + Math.random() * 200,
}));

export default function FeatureChart() {
  return (
    <div className="rounded-xl bg-zinc-900 p-6">
      <h2 className="text-xs font-black uppercase tracking-widest text-zinc-500 mb-4">
        Engineered Features — Last 20 Readings
      </h2>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={SAMPLE_DATA} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="index" stroke="#52525b" tick={{ fill: "#71717a", fontSize: 11 }} />
          <YAxis yAxisId="left" stroke="#52525b" tick={{ fill: "#71717a", fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" stroke="#52525b" tick={{ fill: "#71717a", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
            labelStyle={{ color: "#a1a1aa" }}
          />
          <Legend wrapperStyle={{ color: "#a1a1aa", fontSize: 12 }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="temp_diff"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Temp Diff (K)"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="mechanical_power"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            name="Power (W)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
