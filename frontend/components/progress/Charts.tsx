"use client";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const axis = { fontSize: 11, fill: "#6B6860" };
const tip = { contentStyle: { borderRadius: 8, border: "1px solid #E5E2DA", fontSize: 12 } };

export function ActivityChart({ data }: { data: { date: string; tasks: number; attempts: number }[] }) {
  const rows = data.map((d) => ({ ...d, day: new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid stroke="#EEECE6" vertical={false} />
        <XAxis dataKey="day" tick={axis} tickLine={false} axisLine={{ stroke: "#E5E2DA" }} />
        <YAxis allowDecimals={false} tick={axis} tickLine={false} axisLine={false} />
        <Tooltip {...tip} cursor={{ fill: "#F2F1EC" }} />
        <Bar dataKey="tasks" name="Tasks done" fill="#1F5C46" radius={[3, 3, 0, 0]} maxBarSize={28} />
        <Bar dataKey="attempts" name="Questions tried" fill="#B9D2C4" radius={[3, 3, 0, 0]} maxBarSize={28} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function InterviewChart({ data }: { data: { date: string; overall: number | null }[] }) {
  const rows = data.map((d, i) => ({ n: `#${i + 1}`, score: d.overall ?? 0 }));
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={rows} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
        <CartesianGrid stroke="#EEECE6" vertical={false} />
        <XAxis dataKey="n" tick={axis} tickLine={false} axisLine={{ stroke: "#E5E2DA" }} />
        <YAxis domain={[0, 5]} tick={axis} tickLine={false} axisLine={false} />
        <Tooltip {...tip} />
        <Line type="monotone" dataKey="score" name="Score /5" stroke="#1F5C46" strokeWidth={2} dot={{ r: 3, fill: "#1F5C46" }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
