import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Text,
} from "recharts";
import type { Lifecycle } from "../types";

interface Props {
  lifecycle: Lifecycle;
}

interface WaterfallBar {
  name: string;
  base: number;
  value: number;
  fill: string;
  isTotal: boolean;
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
];

const NAVY = "#1b3a5c";
const STEEL = "#4a7ba7";

function formatDollars(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function buildWaterfallData(lifecycle: Lifecycle): WaterfallBar[] {
  const { b2b } = lifecycle;
  const bars: WaterfallBar[] = [];

  bars.push({
    name: "Gross Payments",
    base: 0,
    value: b2b.gross,
    fill: NAVY,
    isTotal: true,
  });

  let running = b2b.gross;
  b2b.stages.forEach((stage, i) => {
    running -= stage.amount;
    bars.push({
      name: stage.label,
      base: running,
      value: stage.amount,
      fill: TEAL_SCALE[Math.min(i, TEAL_SCALE.length - 1)],
      isTotal: false,
    });
  });

  bars.push({
    name: "Net Received",
    base: 0,
    value: b2b.net,
    fill: STEEL,
    isTotal: true,
  });

  return bars;
}

function ValueLabel(props: {
  x?: number;
  y?: number;
  width?: number;
  value?: number;
  index?: number;
  data: WaterfallBar[];
}) {
  const { x = 0, y = 0, width = 0, index = 0, data } = props;
  const bar = data[index];
  if (!bar) return null;

  const label = formatDollars(bar.value);
  const isDeduction = !bar.isTotal;

  return (
    <Text
      x={x + width / 2}
      y={isDeduction ? y - 6 : y + 14}
      textAnchor="middle"
      fontSize={12}
      fontFamily="'Source Sans 3', sans-serif"
      fill="#2a2a2a"
    >
      {label}
    </Text>
  );
}

export function WaterfallChart({ lifecycle }: Props) {
  const data = buildWaterfallData(lifecycle);

  return (
    <ResponsiveContainer width="100%" height={420}>
      <BarChart
        data={data}
        margin={{ top: 24, right: 12, bottom: 60, left: 12 }}
        barCategoryGap="20%"
      >
        <CartesianGrid
          strokeDasharray=""
          stroke="#e5e0d8"
          vertical={false}
        />
        <XAxis
          dataKey="name"
          tick={{
            fontSize: 11,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#6b6b6b",
          }}
          tickLine={false}
          axisLine={{ stroke: "#e5e0d8" }}
          angle={-35}
          textAnchor="end"
          height={60}
        />
        <YAxis
          tickFormatter={(v: number) => formatDollars(v)}
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#6b6b6b",
          }}
          tickLine={false}
          axisLine={false}
          width={65}
        />
        <Bar dataKey="base" stackId="a" fill="transparent" isAnimationActive={false} />
        <Bar
          dataKey="value"
          stackId="a"
          isAnimationActive={false}
          label={<ValueLabel data={data} />}
        >
          {data.map((bar, i) => (
            <Cell key={i} fill={bar.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
