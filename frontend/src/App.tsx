import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  AudioLines,
  Captions,
  Check,
  ChevronDown,
  CircleAlert,
  Download,
  FileAudio,
  Info,
  LoaderCircle,
  Mic,
  Pause,
  Play,
  StopCircle,
  Trash2,
  Upload,
} from "lucide-react";

import { DEFAULT_SYNTHESIS_SPEED, requestSynthesis, requestTranscription, type ModelId, type SynthesisResult } from "./api";
import { createRecordingFile, formatDuration, getSupportedRecordingMimeType } from "./recording";
import { decodeTake, type Take } from "./waveform";

type ModelOption = { id: ModelId; label: string };

const MAX_REFERENCE_SECONDS = 15;
const RECOMMENDED_SECONDS = [4, 8] as const;
const TRACK_BARS = 96;

const fallbackModels: ModelOption[] = [
  { id: "v1", label: "V1 อ่านภาษาไทยทั่วไป" },
  { id: "v2", label: "V2 ลดการอ่านข้ามและอ่านซ้ำ" },
];

const allowedReferenceExtensions = [".wav", ".mp3", ".m4a", ".flac", ".webm"];

function App() {
  const fileInput = useRef<HTMLInputElement>(null);
  const resultPanel = useRef<HTMLElement>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const recordingStream = useRef<MediaStream | null>(null);
  const recordingTimer = useRef<number | null>(null);
  const recordingStartedAt = useRef<number | null>(null);
  const recordingChunks = useRef<Blob[]>([]);
  const startingRecording = useRef(false);
  const transcriptionRequest = useRef(0);
  const [reference, setReference] = useState<File | null>(null);
  const [referenceUrl, setReferenceUrl] = useState<string | null>(null);
  const [referenceDuration, setReferenceDuration] = useState<number | null>(null);
  const [referenceText, setReferenceText] = useState("");
  const [text, setText] = useState("");
  const [model, setModel] = useState<ModelId>("v1");
  const [speed, setSpeed] = useState(DEFAULT_SYNTHESIS_SPEED);
  const [models, setModels] = useState<ModelOption[]>(fallbackModels);
  const [loadingModels, setLoadingModels] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SynthesisResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    let active = true;
    fetch("/api/models")
      .then(async (response) => {
        if (!response.ok) throw new Error("models unavailable");
        return (await response.json()) as { models: ModelOption[] };
      })
      .then((payload) => {
        if (active && payload.models?.length) setModels(payload.models);
      })
      .catch(() => {
        // The local form remains usable with the known model options if the API is starting.
      })
      .finally(() => {
        if (active) setLoadingModels(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!reference) {
      setReferenceUrl(null);
      return undefined;
    }
    const url = URL.createObjectURL(reference);
    setReferenceUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [reference]);

  useEffect(() => {
    if (result) resultPanel.current?.scrollIntoView({ block: "nearest" });
  }, [result]);

  useEffect(() => () => {
    if (recordingTimer.current !== null) window.clearInterval(recordingTimer.current);
    if (mediaRecorder.current) {
      mediaRecorder.current.onstop = null;
      mediaRecorder.current.onerror = null;
      if (mediaRecorder.current.state !== "inactive") mediaRecorder.current.stop();
    }
    recordingStream.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const stopRecordingTracks = () => {
    recordingStream.current?.getTracks().forEach((track) => track.stop());
    recordingStream.current = null;
    mediaRecorder.current = null;
  };

  const clearRecordingTimer = () => {
    if (recordingTimer.current !== null) {
      window.clearInterval(recordingTimer.current);
      recordingTimer.current = null;
    }
    recordingStartedAt.current = null;
  };

  const stopRecording = () => {
    clearRecordingTimer();
    if (mediaRecorder.current && mediaRecorder.current.state !== "inactive") {
      mediaRecorder.current.stop();
      return;
    }
    stopRecordingTracks();
    setIsRecording(false);
  };

  const cancelTranscription = () => {
    transcriptionRequest.current += 1;
    setIsTranscribing(false);
  };

  const chooseFile = (file?: File) => {
    if (!file) return;
    const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (!allowedReferenceExtensions.includes(extension)) {
      setError("รองรับเฉพาะไฟล์ WAV MP3 M4A FLAC และ WebM");
      return;
    }
    cancelTranscription();
    setError("");
    setResult(null);
    setReferenceDuration(null);
    setReferenceText("");
    setReference(file);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
  };

  const startRecording = async () => {
    if (isRecording || startingRecording.current) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("เบราว์เซอร์นี้อัดเสียงไม่ได้ ลองใช้ Chrome หรือ Edge รุ่นล่าสุด");
      return;
    }
    const mimeType = getSupportedRecordingMimeType();
    if (!mimeType) {
      setError("เบราว์เซอร์นี้อัดเสียงไม่ได้ ให้เลือกไฟล์เสียงแทน");
      return;
    }
    startingRecording.current = true;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType });
      recordingStream.current = stream;
      mediaRecorder.current = recorder;
      recordingChunks.current = [];
      recordingStartedAt.current = Date.now();
      setRecordingSeconds(0);
      setError("");
      setResult(null);
      setIsRecording(true);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) recordingChunks.current.push(event.data);
      };
      recorder.onerror = () => {
        setError("อัดเสียงไม่สำเร็จ ตรวจไมโครโฟนแล้วลองอีกครั้ง");
        clearRecordingTimer();
        stopRecordingTracks();
        setIsRecording(false);
      };
      recorder.onstop = () => {
        const blob = new Blob(recordingChunks.current, { type: recorder.mimeType || mimeType });
        clearRecordingTimer();
        stopRecordingTracks();
        setIsRecording(false);
        if (blob.size > 0) chooseFile(createRecordingFile(blob));
      };
      recorder.start();
      recordingTimer.current = window.setInterval(() => {
        const elapsed = recordingStartedAt.current
          ? Math.floor((Date.now() - recordingStartedAt.current) / 1000)
          : 0;
        setRecordingSeconds(elapsed);
        if (elapsed >= 15) stopRecording();
      }, 250);
    } catch (caught) {
      clearRecordingTimer();
      stopRecordingTracks();
      setIsRecording(false);
      if (caught instanceof DOMException && caught.name === "NotAllowedError") {
        setError("เบราว์เซอร์ยังไม่อนุญาตให้ใช้ไมโครโฟน เปิดสิทธิ์แล้วลองอีกครั้ง");
      } else {
        setError("เปิดไมโครโฟนไม่ได้ ตรวจว่าเสียบไว้และไม่มีแอปอื่นใช้อยู่");
      }
    } finally {
      startingRecording.current = false;
    }
  };

  const clearFile = () => {
    cancelTranscription();
    setReference(null);
    setReferenceDuration(null);
    setReferenceText("");
    setResult(null);
    setError("");
    if (fileInput.current) fileInput.current.value = "";
  };

  const transcribeReference = async () => {
    if (!reference) return;
    const request = ++transcriptionRequest.current;
    setIsTranscribing(true);
    setError("");
    try {
      const payload = await requestTranscription(reference);
      if (request !== transcriptionRequest.current) return;
      setReferenceText(payload.text);
      if (payload.duration > 0) setReferenceDuration(payload.duration);
    } catch (caught) {
      if (request !== transcriptionRequest.current) return;
      setError(caught instanceof Error ? caught.message : "ถอดข้อความไม่สำเร็จ พิมพ์เองได้เลย");
    } finally {
      if (request === transcriptionRequest.current) setIsTranscribing(false);
    }
  };

  const durationInvalid = referenceDuration !== null && (referenceDuration < 2 || referenceDuration > 15);
  const generateBlocker = isRecording
    ? "หยุดอัดก่อนจึงจะสร้างเสียงได้"
    : !reference
      ? "อัดหรือเลือกเสียงต้นฉบับก่อน"
      : durationInvalid
        ? "เสียงต้นฉบับต้องยาว 2 ถึง 15 วินาที เลือกไฟล์ใหม่หรืออัดใหม่"
        : !referenceText.trim() || !text.trim()
          ? "พิมพ์ข้อความให้ครบทั้งสองช่อง"
          : "";
  const canGenerate = !generateBlocker && !isGenerating;

  const handleSubmit = async () => {
    if (!reference || generateBlocker) {
      setError(generateBlocker);
      return;
    }
    setIsGenerating(true);
    setError("");
    setResult(null);
    try {
      const payload = await requestSynthesis({
        reference,
        referenceText,
        text,
        model,
        speed,
      });
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "สร้างเสียงไม่สำเร็จ ลองอีกครั้ง");
    } finally {
      setIsGenerating(false);
    }
  };

  const sourceReady = Boolean(reference) && !durationInvalid && Boolean(referenceText.trim()) && !isRecording;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="topbar-row">
            <a className="brand" href="/" aria-label="ด็อปเปิลเก็งเงอร์ หน้าแรก">
              <span className="brand-mark" aria-hidden="true"><AudioLines size={18} strokeWidth={2.4} /></span>
              <span>ด็อปเปิลเก็งเงอร์</span>
            </a>
          </div>
          <h1 id="page-title">สร้างเสียงพูดภาษาไทยด้วยเสียงของคุณเอง</h1>
        </div>
      </header>

      <main className="workbench" aria-labelledby="page-title">
        <div className="steps">
          <section className="step" aria-labelledby="source-title">
            <StepHead number={1} id="source-title" title="เสียงต้นฉบับ" done={sourceReady} />

            <div
              className={`source${isDragging ? " is-dragging" : ""}`}
              onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setIsDragging(false); }}
              onDrop={handleDrop}
            >
              <input ref={fileInput} className="sr-only" id="reference-file" type="file" tabIndex={-1} aria-label="เลือกไฟล์เสียงต้นฉบับ" accept=".wav,.mp3,.m4a,.flac,.webm,audio/*" onChange={handleFileChange} />

              <TakeTrack src={referenceUrl} label="เสียงต้นฉบับ" scaleSeconds={MAX_REFERENCE_SECONDS} liveSeconds={isRecording ? recordingSeconds : undefined} onDuration={setReferenceDuration} />

              {reference && (
                <div className="file-row">
                  <FileAudio className="file-icon" size={20} aria-hidden="true" />
                  <div className="file-details">
                    <strong title={reference.name}>{reference.name}</strong>
                    <span className={durationInvalid ? "is-invalid" : undefined}>
                      {referenceDuration === null ? "กำลังอ่านความยาว" : `ยาว ${formatDuration(referenceDuration)}`}
                    </span>
                  </div>
                  <button className="icon-button" type="button" onClick={clearFile} disabled={isRecording} aria-label="ลบไฟล์เสียงต้นฉบับ" title="ลบไฟล์">
                    <Trash2 size={18} aria-hidden="true" />
                  </button>
                </div>
              )}

              <div className="source-actions">
                <button className={`button record-button${isRecording ? " is-recording" : ""}`} type="button" onClick={isRecording ? stopRecording : startRecording}>
                  {isRecording ? <StopCircle size={18} aria-hidden="true" /> : <Mic size={18} aria-hidden="true" />}
                  {isRecording ? `หยุดอัด ${formatDuration(recordingSeconds)}` : "อัดเสียง"}
                </button>
                <button className="button" type="button" onClick={() => fileInput.current?.click()} disabled={isRecording}>
                  <Upload size={18} aria-hidden="true" />
                  {reference ? "เปลี่ยนไฟล์เสียง" : "เลือกไฟล์เสียง"}
                </button>
              </div>
              <p className="field-help">
                แนะนำให้ยาว 4 ถึง 8 วินาที<span className="drop-hint"> ลากไฟล์มาวางก็ได้</span>
              </p>
            </div>

            <div className="field-group">
              <div className="label-row">
                <label htmlFor="reference-text">เสียงนี้พูดว่าอะไร</label>
                {reference && (
                  <button className="text-button" type="button" onClick={transcribeReference} disabled={isTranscribing || isRecording}>
                    {isTranscribing ? <><LoaderCircle className="spin" size={16} aria-hidden="true" /> กำลังถอดข้อความ</> : <><Captions size={16} aria-hidden="true" /> ถอดข้อความอัตโนมัติ</>}
                  </button>
                )}
              </div>
              <textarea
                id="reference-text"
                value={referenceText}
                onChange={(event) => setReferenceText(event.target.value)}
                rows={2}
                aria-describedby="reference-help"
              />
              <span className="field-help" id="reference-help">พิมพ์ให้ตรงกับที่พูดทุกคำ คำอังกฤษให้เขียนเป็นคำอ่านไทย</span>
            </div>
          </section>

          <section className="step" aria-labelledby="text-title">
            <StepHead number={2} id="text-title" title="ข้อความที่จะพูด" done={Boolean(text.trim())} />

            <div className="field-group">
              <label className="sr-only" htmlFor="generation-text">ข้อความที่จะพูด</label>
              <textarea
                id="generation-text"
                value={text}
                onChange={(event) => setText(event.target.value.slice(0, 500))}
                placeholder="พิมพ์สิ่งที่อยากให้พูด"
                rows={4}
                maxLength={500}
                aria-describedby="generation-help"
              />
              <div className="label-row">
                <span className="field-help" id="generation-help">ใส่ลูกน้ำหรือจุดตรงที่อยากให้เว้นจังหวะ</span>
                <span className={`character-count${text.length >= 500 ? " is-limit" : ""}`}>{text.length}/500</span>
              </div>
            </div>

            <details className="settings">
              <summary>
                <span>ตั้งค่าเสียง</span>
                <span className="settings-value">{model.toUpperCase()} ความเร็ว {speed.toFixed(2)} เท่า</span>
                <ChevronDown size={18} aria-hidden="true" />
              </summary>
              <div className="controls-row">
                <div className="field-group">
                  <label htmlFor="model">โมเดล</label>
                  <div className="select-wrap">
                    <select id="model" value={model} onChange={(event) => setModel(event.target.value as ModelId)} disabled={loadingModels}>
                      {models.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
                    </select>
                    <ChevronDown size={16} aria-hidden="true" />
                  </div>
                </div>
                <div className="field-group">
                  <label htmlFor="speed">ความเร็ว <span className="value-badge">{speed.toFixed(2)} เท่า</span></label>
                  <input id="speed" type="range" min="0.7" max="1.2" step="0.05" value={speed} onChange={(event) => setSpeed(Number(event.target.value))} />
                  <div className="range-labels"><span>ช้าลง</span><span>เร็วขึ้น</span></div>
                </div>
              </div>
            </details>
          </section>

          <div className="action-bar">
            {error && <div className="error-message" role="alert"><CircleAlert size={18} aria-hidden="true" /><span>{error}</span></div>}
            {generateBlocker && !error && <p className="submit-hint">{generateBlocker}</p>}
            <div className="submit-row">
              <button className="primary-button" type="button" onClick={handleSubmit} disabled={!canGenerate}>
                {isGenerating ? <><LoaderCircle className="spin" size={19} aria-hidden="true" /> กำลังสร้างเสียง</> : <><AudioLines size={19} aria-hidden="true" /> สร้างเสียง</>}
              </button>
            </div>
          </div>
        </div>

        <section ref={resultPanel} className="result-panel" aria-labelledby="result-title" aria-live="polite">
          <StepHead number={3} id="result-title" title="เสียงที่สร้าง" done={Boolean(result)} />
          {result ? (
            <div className="result-content">
              {result.warning && <p className="warning-note"><Info size={16} aria-hidden="true" /> {result.warning}</p>}
              <TakeTrack src={result.audio_url} label="เสียงที่สร้าง" />
              <span className="synthetic-mark">เสียงสังเคราะห์</span>
              <a className="download-button" href={result.audio_url} download><Download size={18} aria-hidden="true" /> ดาวน์โหลดไฟล์ WAV</a>
            </div>
          ) : isGenerating ? (
            <div className="empty-state">
              <LoaderCircle className="spin" size={28} aria-hidden="true" />
              <strong>กำลังสร้างเสียง</strong>
              <p>ครั้งแรกอาจใช้เวลาหลายนาที เพราะต้องโหลดโมเดล</p>
            </div>
          ) : (
            <div className="empty-state">
              <strong>เสียงที่สร้างจะขึ้นตรงนี้</strong>
            </div>
          )}
          <p className="disclaimer">ใช้เสียงของตัวเองหรือเสียงที่เจ้าของอนุญาตเท่านั้น และอย่านำไปอ้างว่าเป็นคำพูดจริงของใคร</p>
        </section>
      </main>

    </div>
  );
}

function StepHead({ number, id, title, done }: { number: number; id: string; title: string; done: boolean }) {
  return (
    <div className="step-head">
      <span className={`step-mark${done ? " is-done" : ""}`} aria-hidden="true">{done ? <Check size={16} strokeWidth={3} /> : number}</span>
      <h2 id={id}>{title}</h2>
      <span className="sr-only">{done ? "พร้อมแล้ว" : "ยังไม่ครบ"}</span>
    </div>
  );
}

type TakeTrackProps = {
  src: string | null;
  label: string;
  scaleSeconds?: number;
  liveSeconds?: number;
  onDuration?: (seconds: number) => void;
};

function TakeTrack({ src, label, scaleSeconds, liveSeconds, onDuration }: TakeTrackProps) {
  const [take, setTake] = useState<Take | null>(null);
  const [position, setPosition] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [decodeFailed, setDecodeFailed] = useState(false);
  const audio = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    setTake(null);
    setPosition(0);
    setPlaying(false);
    setDecodeFailed(false);
    if (!src) return undefined;
    let active = true;
    fetch(src)
      .then((response) => response.arrayBuffer())
      .then((data) => decodeTake(data, TRACK_BARS))
      .then((decoded) => {
        if (!active) return;
        setTake(decoded);
        onDuration?.(decoded.duration);
      })
      .catch(() => {
        // Without a waveform there is nothing to seek on, so hand playback to the native controls.
        if (active) setDecodeFailed(true);
      });
    return () => {
      active = false;
    };
  }, [src, onDuration]);

  const togglePlayback = () => {
    if (!audio.current) return;
    if (playing) audio.current.pause();
    else void audio.current.play();
  };

  const seek = (seconds: number) => {
    if (audio.current) audio.current.currentTime = seconds;
    setPosition(seconds);
  };

  const span = scaleSeconds ?? take?.duration ?? 0;
  const toPercent = (seconds: number) => (span > 0 ? `${Math.min(100, (seconds / span) * 100)}%` : "0%");
  const ruler: { label: string; left?: string }[] = scaleSeconds
    ? [0, 5, 10, scaleSeconds].map((seconds) => ({ label: seconds === scaleSeconds ? `${seconds} วิ` : String(seconds), left: toPercent(seconds) }))
    : [{ label: "00:00" }, { label: formatDuration(take?.duration ?? 0) }];

  return (
    <div className="take">
      <div>
        <div className="track">
          {scaleSeconds && <div className="track-zone" style={{ left: toPercent(RECOMMENDED_SECONDS[0]), width: toPercent(RECOMMENDED_SECONDS[1] - RECOMMENDED_SECONDS[0]) }} />}
          {take && (
            <svg className="track-bars" style={{ width: toPercent(take.duration) }} viewBox={`0 0 ${take.peaks.length} 100`} preserveAspectRatio="none" aria-hidden="true">
              {take.peaks.map((peak, index) => {
                const height = Math.max(3, peak * 88);
                const played = position > 0 && (index + 0.5) / take.peaks.length <= position / take.duration;
                return <rect key={index} className={played ? "is-played" : undefined} x={index + 0.15} y={50 - height / 2} width={0.7} height={height} />;
              })}
            </svg>
          )}
          {liveSeconds !== undefined && <div className="track-live" style={{ width: toPercent(liveSeconds) }} />}
          {take && position > 0 && <div className="track-head" style={{ left: toPercent(position) }} />}
          {take && (
            <input
              className="track-seek"
              style={{ width: toPercent(take.duration) }}
              type="range"
              min={0}
              max={take.duration}
              step={0.25}
              value={Math.min(position, take.duration)}
              onChange={(event) => seek(Number(event.target.value))}
              aria-label={`เลื่อนตำแหน่ง${label}`}
              aria-valuetext={formatDuration(position)}
            />
          )}
        </div>
        <div className={`track-ruler${scaleSeconds ? " is-scaled" : ""}`} aria-hidden="true">
          {ruler.map(({ label, left }, index) => <span key={index} style={left ? { left } : undefined}>{label}</span>)}
        </div>
      </div>
      {src && !decodeFailed && (
        <div className="player">
          <button className="play-button" type="button" onClick={togglePlayback} disabled={!take} aria-label={playing ? `หยุด${label}ชั่วคราว` : `เล่น${label}`}>
            {playing ? <Pause size={22} fill="currentColor" aria-hidden="true" /> : <Play size={22} fill="currentColor" aria-hidden="true" />}
          </button>
          <span className="player-time" aria-hidden="true">{formatDuration(position)} / {formatDuration(take?.duration ?? 0)}</span>
        </div>
      )}
      {src && (
        <audio
          ref={audio}
          controls={decodeFailed}
          src={src}
          preload="metadata"
          onPlay={(event) => {
            setPlaying(true);
            const current = event.currentTarget;
            document.querySelectorAll("audio").forEach((other) => { if (other !== current) other.pause(); });
          }}
          onPause={() => setPlaying(false)}
          onTimeUpdate={(event) => setPosition(event.currentTarget.currentTime)}
          onLoadedMetadata={(event) => {
            const { duration } = event.currentTarget;
            if (Number.isFinite(duration)) onDuration?.(duration);
          }}
        >เบราว์เซอร์นี้ไม่รองรับการเล่นเสียง</audio>
      )}
    </div>
  );
}

export default App;
