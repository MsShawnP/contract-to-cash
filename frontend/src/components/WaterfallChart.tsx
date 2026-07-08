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
import { formatDollars } from "../chartConstants";

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

const NAVY = "#1f2e7a";
const DEDUCTION = "#8e9ad0"; // Chicago-40 blue tint — deductions are ink-light, never a red fill
const RESIDUAL = "#c9c6bf";  // muted grey — unreconciled gross-to-net residual, not an itemized deduction

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
  b2b.stages.forEach((stage) => {
    const isResidual = (stage.count ?? 0) === 0;
    running -= stage.amount;
    bars.push({
      name: isResidual ? "Unreconciled" : stage.label,
      base: running,
      value: stage.amount,
      fill: isResidual ? RESIDUAL : DEDUCTION,
      isTotal: false,
    });
  });

  bars.push({
    name: "Net Received",
    base: 0,
    value: b2b.net,
    fill: NAVY,
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

  return (
    <Text
      x={x + width / 2}
      y={y - 6}
      textAnchor="middle"
      fontSize={12}
      fontFamily="'Source Sans 3', sans-serif"
      fill="#333333"
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
          stroke="#d9d9d9"
          vertical={false}
        />
        <XAxis
          dataKey="name"
          tick={{
            fontSize: 11,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#595959",
          }}
          tickLine={false}
          axisLine={{ stroke: "#d9d9d9" }}
          angle={-35}
          textAnchor="end"
          height={60}
        />
        <YAxis
          tickFormatter={(v: number) => formatDollars(v)}
          tick={{
            fontSize: 12,
            fontFamily: "'Source Sans 3', sans-serif",
            fill: "#595959",
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
