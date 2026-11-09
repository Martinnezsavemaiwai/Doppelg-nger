export type Take = { peaks: number[]; duration: number };

/** Reduces samples to `count` absolute peaks, scaled so the loudest is 1. */
export function computePeaks(samples: ArrayLike<number>, count: number): number[] {
  if (samples.length === 0 || count <= 0) return [];
  const bucketSize = samples.length / count;
  const peaks = Array.from({ length: count }, (_, bucket) => {
    const start = Math.floor(bucket * bucketSize);
    const end = Math.max(start + 1, Math.floor((bucket + 1) * bucketSize));
    let peak = 0;
    for (let index = start; index < end && index < samples.length; index += 1) {
      peak = Math.max(peak, Math.abs(samples[index]));
    }
    return peak;
  });
  const loudest = peaks.reduce((highest, peak) => Math.max(highest, peak), 0);
  return loudest > 0 ? peaks.map((peak) => peak / loudest) : peaks;
}

export async function decodeTake(data: ArrayBuffer, count: number): Promise<Take> {
  const decoded = await new OfflineAudioContext(1, 1, 44100).decodeAudioData(data);
  return { peaks: computePeaks(decoded.getChannelData(0), count), duration: decoded.duration };
}
