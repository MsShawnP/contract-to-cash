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
import { pickTealColor } from "../chartConstants";

interface Props {
  timeToCash: RetailerTimeToCash[];
}

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
          stroke="#d9d9d9"
          horizontal={false}
        />
        <XAxis
          type="number"
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#595959",
          }}
          tickLine={false}
          axisLine={{ stroke: "#d9d9d9" }}
          label={{
            value: "Days",
            position: "insideBottomRight",
            offset: -5,
            style: { fontSize: 11, fill: "#595959", fontFamily: "'Source Sans 3', sans-serif" },
          }}
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
        <Bar dataKey="avg_days" isAnimationActive={false}>
          {sorted.map((_row, i) => (
            <Cell
              key={i}
              fill={pickTealColor(i, sorted.length)}
            />
          ))}
          <LabelList
            dataKey="avg_days"
            position="right"
            formatter={(v: number) => `${Math.round(v)}d`}
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
