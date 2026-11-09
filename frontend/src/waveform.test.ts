import { describe, expect, it } from "vitest";

import { computePeaks } from "./waveform";

describe("computePeaks", () => {
  it("keeps the absolute peak of each bucket, scaled to the loudest", () => {
    expect(computePeaks([0.1, -0.5, 0.25, 0.125], 2)).toEqual([1, 0.5]);
  });

  it("handles more buckets than samples, silence and empty input", () => {
    expect(computePeaks([1], 3)).toEqual([1, 1, 1]);
    expect(computePeaks([0, 0], 2)).toEqual([0, 0]);
    expect(computePeaks([], 4)).toEqual([]);
  });
});
