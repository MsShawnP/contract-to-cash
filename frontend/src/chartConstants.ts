export const TEAL_SCALE = [
  "#063d32",
  "#0a5c4b",
  "#0e6e5a",
  "#158f75",
  "#1fa282",
  "#35b595",
  "#6dcdb5",
  "#b5e4d8",
] as const;

export function formatDollars(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

export function pickTealColor(index: number, total: number): string {
  const colorIdx = Math.min(
    Math.round((index / Math.max(total - 1, 1)) * (TEAL_SCALE.length - 1)),
    TEAL_SCALE.length - 1,
  );
  return TEAL_SCALE[colorIdx];
}
