import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import type { RetailerLeakage } from "../types";

interface Props {
  retailers: RetailerLeakage[];
}

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
          stroke="#d9d9d9"
          horizontal={false}
        />
        <XAxis
          type="number"
          tickFormatter={(v: number) => `${v}%`}
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#595959",
          }}
          tickLine={false}
          axisLine={{ stroke: "#d9d9d9" }}
          domain={[0, "auto"]}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#333333",
          }}
          tickLine={false}
          axisLine={false}
          width={130}
        />
        <Bar dataKey="leakage_pct" fill="#1f2e7a" isAnimationActive={false}>
          <LabelList
            dataKey="leakage_pct"
            position="right"
            formatter={(v: number) => `${v.toFixed(1)}%`}
            style={{
              fontSize: 12,
              fontFamily: "'Source Sans 3', sans-serif",
              fill: "#333333",
            }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
