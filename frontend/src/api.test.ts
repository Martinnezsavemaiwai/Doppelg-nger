import { describe, expect, it, vi } from "vitest";

import {
  buildSynthesisFormData,
  requestSynthesis,
  requestTranscription,
  type SynthesisInput,
} from "./api";

const input: SynthesisInput = {
  reference: new File(["RIFF"], "voice.wav", { type: "audio/wav" }),
  referenceText: "สวัสดีครับ",
  text: "ทดลองเสียง",
};

describe("voice synthesis API client", () => {
  it("maps the form state to the backend multipart contract", () => {
    const form = buildSynthesisFormData(input);

    expect(form.get("reference")).toBe(input.reference);
    expect(form.get("reference_text")).toBe("สวัสดีครับ");
    expect(form.get("text")).toBe("ทดลองเสียง");
    expect([...form.keys()]).toEqual(["reference", "reference_text", "text"]);
  });

  it("returns the synthesis payload and turns failed responses into a readable error", async () => {
    const fetcher = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ status: "สร้างเสียงเรียบร้อย", warning: null, audio_url: "/api/outputs/a.wav" }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "กรุณาพิมพ์ข้อความที่จะพูด" }), { status: 400 }),
      );

    await expect(requestSynthesis(input, fetcher)).resolves.toEqual({
      status: "สร้างเสียงเรียบร้อย",
      warning: null,
      audio_url: "/api/outputs/a.wav",
    });
    await expect(requestSynthesis(input, fetcher)).rejects.toThrow(
      "กรุณาพิมพ์ข้อความที่จะพูด",
    );
  });

  it("uploads a reference file for local transcription", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ text: "สวัสดีครับ", duration: 5.4, language: "th" }), { status: 200 }),
    );

    await expect(requestTranscription(input.reference, fetcher)).resolves.toEqual({
      text: "สวัสดีครับ",
      duration: 5.4,
      language: "th",
    });
    const body = fetcher.mock.calls[0][1]?.body as FormData;
    expect(body.get("reference")).toBe(input.reference);
  });
});
