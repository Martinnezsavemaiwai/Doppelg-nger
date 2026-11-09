from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def run_powershell(script, *args):
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / script),
            *args,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_setup_check_only_validates_host_without_installing():
    result = run_powershell("setup.ps1", "-CheckOnly", "-MinimumFreeGB", "0")
    assert result.returncode == 0, result.stderr
    assert "Python" in result.stdout
    assert "FFmpeg" in result.stdout
    assert "Nothing was installed" in result.stdout


def test_setup_check_only_does_not_create_the_runtime_junction(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "setup.ps1").write_bytes((ROOT / "setup.ps1").read_bytes())

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(project / "setup.ps1"),
            "-CheckOnly",
            "-MinimumFreeGB",
            "0",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "DoppelgangerRuntime").exists()


def test_setup_import_checks_keep_native_backends_in_separate_processes():
    source = (ROOT / "setup.ps1").read_text(encoding="utf-8")

    assert "import torch, gradio, soundfile, f5_tts_th, faster_whisper" not in source
    assert "import torch, gradio, soundfile, f5_tts_th" in source
    assert "import faster_whisper" in source


def test_run_backend_dry_run_reports_api_entrypoint_without_environment():
    result = run_powershell("run-backend.ps1", "-DryRun")
    assert result.returncode == 0, result.stderr
    assert "thai_voice_clone.api:app" in result.stdout
    assert "127.0.0.1:8000" in result.stdout
    assert "DoppelgangerRuntime" in result.stdout


def test_run_frontend_dry_run_reports_vite_entrypoint_without_environment():
    result = run_powershell("run-frontend.ps1", "-DryRun")
    assert result.returncode == 0, result.stderr
    assert "npm run dev" in result.stdout
    assert "127.0.0.1:5173" in result.stdout
    assert "frontend" in result.stdout


def test_run_legacy_dry_run_keeps_gradio_fallback():
    result = run_powershell("run-legacy.ps1", "-DryRun")
    assert result.returncode == 0, result.stderr
    assert "thai_voice_clone.app" in result.stdout
    assert "127.0.0.1:7860" in result.stdout


def test_run_dry_run_describes_both_local_services():
    result = run_powershell("run.ps1", "-DryRun")
    assert result.returncode == 0, result.stderr
    assert "127.0.0.1:8000" in result.stdout
    assert "127.0.0.1:5173" in result.stdout
