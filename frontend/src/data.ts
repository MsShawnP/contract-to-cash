import type { Summary, Lifecycle, Retailers } from "./types";

const BASE = import.meta.env.BASE_URL + "json/";

async function fetchJson<T>(filename: string): Promise<T> {
  const res = await fetch(BASE + filename);
  if (!res.ok) throw new Error(`Failed to load ${filename}: ${res.status}`);
  return res.json() as Promise<T>;
}

export async function loadData() {
  const [summary, lifecycle, retailers] = await Promise.all([
    fetchJson<Summary>("summary.json"),
    fetchJson<Lifecycle>("lifecycle.json"),
    fetchJson<Retailers>("retailers.json"),
  ]);
  return { summary, lifecycle, retailers };
}

export type AppData = Awaited<ReturnType<typeof loadData>>;
