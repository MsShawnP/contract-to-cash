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

const NAVY = "#1b3a5c";
const STEEL = "#4a7ba7";

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
          {sorted.map((row, i) => (
            <Cell key={i} fill={row.avg_days > 50 ? NAVY : STEEL} />
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
