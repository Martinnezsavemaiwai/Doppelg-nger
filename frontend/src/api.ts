export type SynthesisInput = {
  reference: File;
  referenceText: string;
  text: string;
};

export type SynthesisResult = {
  status: string;
  warning: string | null;
  audio_url: string;
};

export type TranscriptionResult = {
  text: string;
  duration: number;
  language: string | null;
};

export function buildSynthesisFormData(input: SynthesisInput): FormData {
  const form = new FormData();
  form.append("reference", input.reference);
  form.append("reference_text", input.referenceText);
  form.append("text", input.text);
  return form;
}

export async function requestSynthesis(
  input: SynthesisInput,
  fetcher: typeof fetch = fetch,
): Promise<SynthesisResult> {
  const response = await fetcher("/api/synthesize", {
    method: "POST",
    body: buildSynthesisFormData(input),
  });
  const payload = (await response.json().catch(() => ({}))) as Partial<SynthesisResult> & {
    detail?: string;
  };
  if (!response.ok) {
    throw new Error(payload.detail || "สร้างเสียงไม่สำเร็จ ลองอีกครั้ง");
  }
  return payload as SynthesisResult;
}

export async function requestTranscription(
  reference: File,
  fetcher: typeof fetch = fetch,
): Promise<TranscriptionResult> {
  const form = new FormData();
  form.append("reference", reference);
  const response = await fetcher("/api/transcribe", {
    method: "POST",
    body: form,
  });
  const payload = (await response.json().catch(() => ({}))) as Partial<TranscriptionResult> & {
    detail?: string;
  };
  if (!response.ok) {
    throw new Error(payload.detail || "ถอดข้อความไม่สำเร็จ พิมพ์เองได้เลย");
  }
  return payload as TranscriptionResult;
}
