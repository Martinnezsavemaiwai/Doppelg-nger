# พัฒนาต่อ

ติดตั้งตาม [README](README.md) ก่อน แล้วค่อยรันแยกทีละส่วนได้:

```powershell
.\run-backend.ps1
.\run-frontend.ps1
```

- ตรวจสถานะ backend: `http://127.0.0.1:8000/api/health`
- เอกสาร API: `http://127.0.0.1:8000/api/docs`
- หน้า Gradio รุ่นเดิมสำหรับ debug: `.\run-legacy.ps1` ที่ `http://127.0.0.1:7860`
- ปิด backend และ frontend ที่เปิดจาก `run.ps1`: `.\stop.ps1`
- `run*.ps1` และ `stop.ps1` รองรับ `-DryRun` เพื่อพิมพ์คำสั่งโดยไม่รันจริง

## โครงสร้าง

- **Backend:** FastAPI และ Uvicorn ที่ `http://127.0.0.1:8000` อยู่ใน `src/thai_voice_clone/`
- **Frontend:** React และ Vite ที่ `http://127.0.0.1:5173` อยู่ใน `frontend/`
- **ตัวถอดข้อความ:** faster-whisper รันใน Python worker แยกโปรเซส เพื่อไม่ให้ native runtime ชนกับ PyTorch และ VoxCPM2 worker เพิ่ม DLL ของ CUDA 12 จาก wheel `nvidia-*-cu12` เข้า PATH ก่อนโหลดโมเดลบน GPU ถ้า GPU ใช้ไม่ได้จะกลับไปใช้ CPU

## ลำดับการสร้างเสียง

เมื่อ frontend ส่ง `POST /api/synthesize` แบบ multipart ที่มี `reference` `reference_text` และ `text`

1. `api.py` บันทึกไฟล์อัปโหลดลงโฟลเดอร์ชั่วคราว
2. `app.generate()` วัดความยาวด้วย `ffprobe` และตรวจข้อมูลด้วย `validation.validate_request`
3. `audio.prepared_reference` แปลงเสียงต้นฉบับเป็นรูปแบบมาตรฐานด้วย `ffmpeg`
4. `model.VoiceCloneService` แบ่งข้อความตามเครื่องหมายวรรคตอน สร้างเสียงทีละวลีด้วย VoxCPM2 (`VoxCPMBackend`) แล้วต่อกันเป็นไฟล์ 48 kHz ตาม sample rate ของโมเดล โดยเว้น 0.32 วินาทีหลังจบประโยค และ 0.16 วินาทีหลังลูกน้ำ
5. บันทึกเป็น `outputs/generated/voice-<เวลา>-<รหัส>.wav` แล้วส่ง URL `/api/outputs/<ชื่อไฟล์>` กลับไป

โมเดล TTS โหลดเมื่อสร้างเสียงครั้งแรกแล้วเก็บไว้ใช้ต่อ `/api/health` จึงตอบได้โดยไม่ต้องโหลดโมเดล ถ้าหน่วยความจำ GPU ไม่พอ ระบบจะทิ้งโมเดลที่โหลดไว้เพื่อให้ลองใหม่ได้

ตอนโหลด `VoxCPMBackend` ตั้ง default dtype เป็น bfloat16 ชั่วคราว เพราะ VoxCPM สร้างโมเดลเป็น float32 ก่อนแปลง ทำให้ commit memory พุ่งถึงราว 16 GB และ crash แบบ access violation บนเครื่อง RAM 16 GB ได้ ถ้าเปลี่ยนเวอร์ชัน `voxcpm` ให้วัดหน่วยความจำตอนโหลดซ้ำ

## ความปลอดภัย

- backend และ frontend รับการเชื่อมต่อเฉพาะที่ `127.0.0.1`
- รับอัปโหลดเฉพาะ `.wav` `.mp3` `.m4a` `.flac` และ `.webm`
- `/api/outputs/{filename}` ส่งให้เฉพาะไฟล์ `.wav` ใน `outputs/generated/` และกัน path traversal
- CORS อนุญาต `http://127.0.0.1:5173` และ `http://localhost:5173` เปลี่ยนได้ด้วย `THAI_VOICE_FRONTEND_ORIGINS` โดยคั่นด้วยลูกน้ำ

## รันเทสต์

```powershell
.\.venv\Scripts\python.exe -m pytest
Push-Location frontend
npm test
npm run build
Pop-Location
```

## ข้อควรรู้

- **Runtime path:** `setup.ps1` สร้าง `DoppelgangerRuntime` ไว้ข้างโฟลเดอร์โปรเจกต์ เป็น junction ที่ชี้กลับมาที่โปรเจกต์ แล้วรัน Python และเก็บ cache ของ Hugging Face ผ่าน path นี้ เพราะชื่อโฟลเดอร์ `Doppelgänger` มีอักษรนอก ASCII ซึ่ง native library บางตัวเปิดไม่ได้
- **เทสต์สคริปต์:** `tests/test_scripts.py` เรียกสคริปต์จริงผ่าน PowerShell จึงต้องมี Python, FFmpeg และ Node.js ใน PATH
- **Dependency:** pin เวอร์ชันไว้ตรงตัวทุกตัว `av` ล็อกไว้ที่ 15.1.0 เพราะ `av` 19 ตัด argument ที่ faster-whisper 1.2.1 ยังใช้ ส่วน torch ติดตั้งจาก index cu126 ใน `setup.ps1`
- **เทสต์ไม่โหลดโมเดลจริง:** `create_api()` และ `generate()` รับ factory หรือฟังก์ชันจากภายนอก ส่วน import หนักอย่าง `torch` `voxcpm` `faster_whisper` และ `gradio` ตั้งใจวางไว้ในฟังก์ชัน
- **Worker ถอดข้อความ:** รันด้วย `python -m thai_voice_clone.transcription_worker <ไฟล์>` แล้วส่งผลกลับทาง stdout หนึ่งบรรทัดในรูป `DOPPELGANGER_TRANSCRIPTION_RESULT:<json>`
- **UI:** แก้หน้าเว็บตาม [DESIGN.md](DESIGN.md) และ [PRODUCT.md](PRODUCT.md)
- **ไฟล์เสียง:** อย่าใช้ `git add -f` กับไฟล์ใน `data/reference/` และ `outputs/generated/`
