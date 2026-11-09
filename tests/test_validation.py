import pytest

from thai_voice_clone.model import split_generation_text
from thai_voice_clone.validation import UserInputError, validate_request


def valid(tmp_path, **changes):
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"RIFF")
    values = {
        "reference": audio,
        "reference_text": "สวัสดีครับ",
        "text": "ทดสอบเสียง",
        "model": "v1",
        "speed": 1.0,
        "duration": 6.0,
    }
    values.update(changes)
    return values


@pytest.mark.parametrize(
    "field,value,needle",
    [
        ("reference_text", "  ", "ข้อความต้นฉบับ"),
        ("text", "", "ข้อความที่ต้องการ"),
        ("text", "... ,!?", "ข้อความที่ต้องการ"),
        ("model", "v3", "โมเดล"),
        ("speed", 0.69, "ความเร็ว"),
        ("speed", 1.21, "ความเร็ว"),
        ("duration", 1.9, "2 ถึง 15"),
        ("duration", 15.1, "2 ถึง 15"),
    ],
)
def test_rejects_invalid_values(tmp_path, field, value, needle):
    with pytest.raises(UserInputError, match=needle):
        validate_request(**valid(tmp_path, **{field: value}))


def test_rejects_unsupported_suffix(tmp_path):
    values = valid(tmp_path)
    values["reference"] = tmp_path / "voice.exe"
    values["reference"].write_bytes(b"x")
    with pytest.raises(UserInputError, match="รองรับเฉพาะไฟล์"):
        validate_request(**values)


def test_accepts_webm_recording_reference(tmp_path):
    values = valid(tmp_path)
    values["reference"] = tmp_path / "recording.webm"
    values["reference"].write_bytes(b"webm")

    request = validate_request(**values)

    assert request.reference.suffix == ".webm"


def test_rejects_more_than_500_characters(tmp_path):
    with pytest.raises(UserInputError, match="500"):
        validate_request(**valid(tmp_path, text="ก" * 501))


def test_normalizes_whitespace_and_warns_for_nonideal_duration(tmp_path):
    request = validate_request(
        **valid(
            tmp_path,
            reference_text=" สวัสดี   ครับ ",
            text=" ทดลอง  เสียง ",
            duration=10.0,
        )
    )
    assert request.reference_text == "สวัสดี ครับ"
    assert request.text == "ทดลอง เสียง"
    assert request.warning is not None


def test_keeps_line_breaks_in_generation_text_so_they_become_pauses(tmp_path):
    request = validate_request(
        **valid(
            tmp_path,
            reference_text="สวัสดี\nครับ",
            text=" บรรทัด   หนึ่ง \n\n  บรรทัดสอง\r\n",
        )
    )

    assert request.reference_text == "สวัสดี ครับ"
    assert request.text == "บรรทัด หนึ่ง\nบรรทัดสอง"
    assert split_generation_text(request.text) == [
        ("บรรทัด หนึ่ง", 0.32),
        ("บรรทัดสอง", 0.0),
    ]


def test_warns_when_reference_text_contains_latin_words(tmp_path):
    request = validate_request(
        **valid(tmp_path, reference_text="สวัสดี Avengers", duration=6.0)
    )

    assert request.warning is not None
    assert "คำอังกฤษ" in request.warning
