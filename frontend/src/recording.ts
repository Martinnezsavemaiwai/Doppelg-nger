export const RECORDING_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
];

export function getSupportedRecordingMimeType(
  mimeTypes: string[] = RECORDING_MIME_TYPES,
  isSupported: (mimeType: string) => boolean = (mimeType) =>
    typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(mimeType),
): string | null {
  return mimeTypes.find((mimeType) => isSupported(mimeType)) ?? null;
}

export function createRecordingFile(blob: Blob, name = "recording.webm"): File {
  return new File([blob], name, { type: blob.type || "audio/webm" });
}

export function formatDuration(seconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(safeSeconds / 60);
  const remainder = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}
