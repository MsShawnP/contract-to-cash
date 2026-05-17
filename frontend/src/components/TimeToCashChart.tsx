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
import type { RetailerTimeToCash } from "../types";

interface Props {
  timeToCash: RetailerTimeToCash[];
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
];

export function TimeToCashChart({ timeToCash }: Props) {
  const sorted = [...timeToCash].sort((a, b) => b.avg_days - a.avg_days);

  return (
    <ResponsiveContainer width="100%" height={360}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 8, right: 50, bottom: 8, left: 8 }}
        barCategoryGap="25%"
      >
        <CartesianGrid
          strokeDasharray=""
          stroke="#e5e0d8"
          horizontal={false}
        />
        <XAxis
          type="number"
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#6b6b6b",
          }}
          tickLine={false}
          axisLine={{ stroke: "#e5e0d8" }}
          label={{
            value: "Days",
            position: "insideBottomRight",
            offset: -5,
            style: { fontSize: 11, fill: "#6b6b6b", fontFamily: "'Source Sans 3', sans-serif" },
          }}
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
        <Bar dataKey="avg_days" isAnimationActive={false}>
          {sorted.map((_row, i) => (
            <Cell
              key={i}
              fill={TEAL_SCALE[Math.min(Math.round((i / Math.max(sorted.length - 1, 1)) * (TEAL_SCALE.length - 1)), TEAL_SCALE.length - 1)]}
            />
          ))}
          <LabelList
            dataKey="avg_days"
            position="right"
            formatter={(v: number) => `${Math.round(v)}d`}
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
