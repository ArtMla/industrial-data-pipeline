interface KpiCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "blue" | "green" | "red" | "zinc";
}

const accentMap = {
  blue: "border-blue-500 text-blue-400",
  green: "border-green-500 text-green-400",
  red: "border-red-500 text-red-400",
  zinc: "border-zinc-600 text-zinc-400",
};

export default function KpiCard({ label, value, sub, accent = "blue" }: KpiCardProps) {
  return (
    <div className={`rounded-xl border-l-4 bg-zinc-900 p-5 ${accentMap[accent]}`}>
      <p className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-1">{label}</p>
      <p className="text-3xl font-black text-white">{value}</p>
      {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
    </div>
  );
}
