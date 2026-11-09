from collections.abc import Callable
from pathlib import Path

from .audio import AudioPreparationError, prepared_reference, probe_duration
from .config import load_settings
from .model import ModelError, create_service
from .validation import UserInputError, validate_request


def generate(
    reference,
    reference_text,
    text,
    duration_probe=probe_duration,
    prepare=prepared_reference,
    service=None,
    output_factory=None,
) -> tuple[str, str, str]:
    if not reference:
        raise UserInputError("กรุณาเลือกไฟล์เสียงต้นฉบับ")
    duration = duration_probe(reference)
    request = validate_request(reference, reference_text, text, duration)
    if service is None or output_factory is None:
        raise RuntimeError("generation dependencies are not configured")
    with prepare(request.reference) as normalized_reference:
        result = service.synthesize(
            request,
            normalized_reference,
            output_factory(),
        )
    status = "สร้างเสียงเรียบร้อย"
    if request.warning:
        status = f"{status} — {request.warning}"
    return status, str(result), str(result)


def build_app(service_factory: Callable = create_service):
    import gradio as gr

    settings = load_settings()
    cached_service = None

    def handle(reference, reference_text, text):
        nonlocal cached_service
        try:
            if cached_service is None:
                cached_service = service_factory(settings)
            return generate(
                reference,
                reference_text,
                text,
                service=cached_service,
                output_factory=settings.new_output_path,
            )
        except (UserInputError, AudioPreparationError, ModelError) as exc:
            raise gr.Error(str(exc)) from exc

    default_reference = None
    if settings.default_reference.is_file():
        default_reference = str(settings.default_reference)

    with gr.Blocks(title="ด็อปเปิลเก็งเงอร์ โคลนเสียงภาษาไทย") as app:
        gr.Markdown("# ด็อปเปิลเก็งเงอร์ (Doppelgänger)")
        gr.Markdown(
            "เครื่องมือนี้ใช้สำหรับเสียงของคุณเองหรือเสียงที่ได้รับอนุญาตเท่านั้น "
            "เสียงที่สร้างขึ้นไม่ใช่หลักฐานว่าบุคคลนั้นเคยพูดข้อความดังกล่าว"
        )
        reference = gr.Audio(
            label="เสียงต้นฉบับ (แนะนำ 4–8 วินาที)",
            type="filepath",
            sources=["upload"],
            value=default_reference,
        )
        reference_text = gr.Textbox(
            label="ข้อความที่พูดในเสียงต้นฉบับ",
            placeholder="กรอกให้ตรงกับเสียงทุกคำ",
        )
        text = gr.Textbox(
            label="ข้อความภาษาไทยที่ต้องการสร้าง",
            lines=4,
            max_lines=8,
        )
        submit = gr.Button("สร้างเสียง", variant="primary")
        status = gr.Markdown()
        output_audio = gr.Audio(label="เสียงที่สร้าง")
        download = gr.File(label="ดาวน์โหลด WAV")
        submit.click(
            handle,
            inputs=[reference, reference_text, text],
            outputs=[status, output_audio, download],
            show_progress="full",
        )
    return app


def main() -> None:
    app = build_app()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
