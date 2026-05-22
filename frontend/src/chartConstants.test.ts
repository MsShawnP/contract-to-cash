import { describe, it, expect } from "vitest";
import { TEAL_SCALE, formatDollars, pickTealColor } from "./chartConstants";

describe("formatDollars", () => {
  it("formats millions", () => {
    expect(formatDollars(1_500_000)).toBe("$1.5M");
    expect(formatDollars(17_400_000)).toBe("$17.4M");
  });

  it("formats thousands", () => {
    expect(formatDollars(1_000)).toBe("$1K");
    expect(formatDollars(55_000)).toBe("$55K");
    expect(formatDollars(999_999)).toBe("$1000K");
  });

  it("formats small values", () => {
    expect(formatDollars(0)).toBe("$0");
    expect(formatDollars(42)).toBe("$42");
    expect(formatDollars(999)).toBe("$999");
  });

  it("handles the million boundary", () => {
    expect(formatDollars(1_000_000)).toBe("$1.0M");
  });
});

describe("pickTealColor", () => {
  it("returns darkest for first of many", () => {
    expect(pickTealColor(0, 8)).toBe(TEAL_SCALE[0]);
  });

  it("returns lightest for last of many", () => {
    expect(pickTealColor(7, 8)).toBe(TEAL_SCALE[7]);
  });

  it("returns darkest when total is 1", () => {
    expect(pickTealColor(0, 1)).toBe(TEAL_SCALE[0]);
  });

  it("returns a middle color for middle index", () => {
    const color = pickTealColor(2, 5);
    expect(TEAL_SCALE).toContain(color);
  });

  it("never returns undefined", () => {
    for (let total = 1; total <= 20; total++) {
      for (let i = 0; i < total; i++) {
        expect(pickTealColor(i, total)).toBeDefined();
      }
    }
  });
});

describe("TEAL_SCALE", () => {
  it("has 8 colors matching Hong Kong design system steps", () => {
    expect(TEAL_SCALE).toHaveLength(8);
  });

  it("all entries are valid hex colors", () => {
    for (const color of TEAL_SCALE) {
      expect(color).toMatch(/^#[0-9a-f]{6}$/);
    }
  });
});
