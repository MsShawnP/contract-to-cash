import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import type { RetailerLeakage } from "../types";

interface Props {
  retailers: RetailerLeakage[];
}

const TEAL_SCALE = [
  "#0A3D3D",
  "#14605C",
  "#1F8078",
  "#2A9D93",
  "#45B5AA",
  "#6BCABD",
  "#93DCD2",
  "#BDEEE8",
  "#D4F4F0",
  "#E8F9F6",
];

export function RetailerChart({ retailers }: Props) {
  const sorted = [...retailers].sort((a, b) => b.leakage_pct - a.leakage_pct);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 8, right: 60, bottom: 8, left: 8 }}
        barCategoryGap="25%"
      >
        <CartesianGrid
          strokeDasharray=""
          stroke="#e5e0d8"
          horizontal={false}
        />
        <XAxis
          type="number"
          tickFormatter={(v: number) => `${v}%`}
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#6b6b6b",
          }}
          tickLine={false}
          axisLine={{ stroke: "#e5e0d8" }}
          domain={[0, "auto"]}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#2a2a2a",
          }}
          tickLine={false}
          axisLine={false}
          width={130}
        />
        <Bar dataKey="leakage_pct" isAnimationActive={false}>
          {sorted.map((_, i) => (
            <Cell key={i} fill={TEAL_SCALE[i % TEAL_SCALE.length]} />
          ))}
          <LabelList
            dataKey="leakage_pct"
            position="right"
            formatter={(v: number) => `${v.toFixed(1)}%`}
            style={{
              fontSize: 12,
              fontFamily: "'Source Sans 3', sans-serif",
              fill: "#2a2a2a",
            }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
