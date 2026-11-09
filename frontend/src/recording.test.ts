import { describe, expect, it } from "vitest";

import {
  createRecordingFile,
  formatDuration,
  getSupportedRecordingMimeType,
} from "./recording";

describe("recording helpers", () => {
  it("chooses the first browser-supported recording MIME type", () => {
    expect(
      getSupportedRecordingMimeType(
        ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"],
        (mimeType) => mimeType === "audio/webm",
      ),
    ).toBe("audio/webm");
  });

  it("returns null when the browser cannot record any supported type", () => {
    expect(getSupportedRecordingMimeType(["audio/webm"], () => false)).toBeNull();
  });

  it("formats elapsed recording time and creates a WebM File", () => {
    expect(formatDuration(68)).toBe("01:08");
    const file = createRecordingFile(new Blob(["audio"], { type: "audio/webm" }), "take.webm");
    expect(file.name).toBe("take.webm");
    expect(file.type).toBe("audio/webm");
  });
});
