from pathlib import Path

from fastapi.testclient import TestClient

from thai_voice_clone import api as api_module
from thai_voice_clone.api import create_api
from thai_voice_clone.config import Settings
from thai_voice_clone.transcription import TranscriptionError, TranscriptionResult


def make_settings(tmp_path: Path) -> Settings:
    return Settings(root=tmp_path, device_mode="cpu")


def test_health_and_models_do_not_load_the_tts_service(tmp_path):
    def fail_if_loaded(_settings):
        raise AssertionError("the model service must be lazy")

    client = TestClient(
        create_api(settings=make_settings(tmp_path), service_factory=fail_if_loaded)
    )

    health = client.get("/api/health")
    models = client.get("/api/models")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert [item["id"] for item in models.json()["models"]] == ["v1", "v2"]


def test_synthesize_accepts_multipart_audio_and_returns_output_url(tmp_path):
    settings = make_settings(tmp_path)
    calls = []

    def fake_generate(reference, reference_text, text, model, speed, **kwargs):
        calls.append(
            {
                "reference": Path(reference),
                "reference_text": reference_text,
                "text": text,
                "model": model,
                "speed": speed,
            }
        )
        output = kwargs["output_factory"]()
        output.write_bytes(b"RIFFfake-wav")
        return "สร้างเสียงเรียบร้อย — แนะนำเสียงต้นฉบับยาว 4 ถึง 8 วินาที", str(output), str(output)

    client = TestClient(
        create_api(
            settings=settings,
            service_factory=lambda _: object(),
            generate_fn=fake_generate,
        )
    )
    response = client.post(
        "/api/synthesize",
        files={"reference": ("voice.wav", b"RIFFreference", "audio/wav")},
        data={
            "reference_text": " สวัสดีครับ ",
            "text": " ทดลองเสียง ",
            "model": "v2",
            "speed": "0.9",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "สร้างเสียงเรียบร้อย"
    assert payload["warning"] == "แนะนำเสียงต้นฉบับยาว 4 ถึง 8 วินาที"
    assert payload["audio_url"].startswith("/api/outputs/")
    assert calls[0]["reference"].suffix == ".wav"
    assert calls[0]["reference_text"] == " สวัสดีครับ "
    assert calls[0]["text"] == " ทดลองเสียง "
    assert calls[0]["model"] == "v2"
    assert calls[0]["speed"] == 0.9


def test_synthesize_accepts_recorded_webm_reference(tmp_path):
    settings = make_settings(tmp_path)

    def fake_generate(*args, **kwargs):
        output = kwargs["output_factory"]()
        output.write_bytes(b"RIFFfake-wav")
        return "สร้างเสียงเรียบร้อย", str(output), str(output)

    client = TestClient(
        create_api(settings=settings, service_factory=lambda _: object(), generate_fn=fake_generate)
    )
    response = client.post(
        "/api/synthesize",
        files={"reference": ("recording.webm", b"webm", "audio/webm")},
        data={"reference_text": "ต้นฉบับ", "text": "ทดลอง"},
    )

    assert response.status_code == 200


def test_transcribe_returns_editable_text_and_metadata(tmp_path):
    client = TestClient(
        create_api(
            settings=make_settings(tmp_path),
            transcribe_fn=lambda path, settings: TranscriptionResult(
                text="สวัสดีครับ วันนี้", duration=6.25, language="th"
            ),
        )
    )

    response = client.post(
        "/api/transcribe",
        files={"reference": ("voice.webm", b"webm", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "text": "สวัสดีครับ วันนี้",
        "duration": 6.25,
        "language": "th",
    }


def test_transcribe_uses_isolated_worker_by_default(tmp_path, monkeypatch):
    created = []

    class FakeSubprocessTranscriber:
        def __init__(self, settings):
            created.append(settings)

        def transcribe(self, path):
            return TranscriptionResult(text="จาก worker", duration=1.0, language="th")

    monkeypatch.setattr(api_module, "SubprocessWhisperTranscriber", FakeSubprocessTranscriber)
    client = TestClient(create_api(settings=make_settings(tmp_path)))

    response = client.post(
        "/api/transcribe",
        files={"reference": ("voice.wav", b"wav", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "จาก worker"
    assert len(created) == 1


def test_transcribe_returns_manual_entry_error_when_model_is_unavailable(tmp_path):
    def unavailable(path, settings):
        raise TranscriptionError("กรุณากรอกข้อความเอง")

    client = TestClient(
        create_api(settings=make_settings(tmp_path), transcribe_fn=unavailable)
    )
    response = client.post(
        "/api/transcribe",
        files={"reference": ("voice.wav", b"wav", "audio/wav")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "กรุณากรอกข้อความเอง"


def test_synthesize_rejects_unsupported_upload_before_model_load(tmp_path):
    def fail_if_loaded(_settings):
        raise AssertionError("the model service must remain unloaded")

    client = TestClient(
        create_api(settings=make_settings(tmp_path), service_factory=fail_if_loaded)
    )
    response = client.post(
        "/api/synthesize",
        files={"reference": ("voice.exe", b"not-audio", "application/octet-stream")},
        data={"reference_text": "ต้นฉบับ", "text": "ทดลอง"},
    )

    assert response.status_code == 400
    assert "WAV" in response.json()["detail"]


def test_output_download_is_contained_to_generated_directory(tmp_path):
    settings = make_settings(tmp_path)
    settings.output_dir.mkdir(parents=True)
    (settings.output_dir / "safe.wav").write_bytes(b"RIFFsafe")
    (tmp_path / "secret.txt").write_text("secret", encoding="utf-8")
    client = TestClient(create_api(settings=settings))

    safe = client.get("/api/outputs/safe.wav")
    traversal = client.get("/api/outputs/%2E%2E%2Fsecret.txt")
    missing = client.get("/api/outputs/missing.wav")

    assert safe.status_code == 200
    assert safe.headers["content-type"] == "audio/wav"
    assert safe.content == b"RIFFsafe"
    assert traversal.status_code == 404
    assert missing.status_code == 404
