# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React/Vite frontend with a local FastAPI backend; selected by the user for the Windows-first project.

## Users

Inferred from the approved brief: the primary user is the project owner, working locally on Windows, who wants to synthesize Thai speech in their own voice from a short reference recording.

## Product Purpose

Inferred from the approved brief: Doppelgänger lets a user provide an authorized voice sample, type Thai text, and create a WAV file locally. Success means the workflow is understandable without developer tools and the generated file can be previewed and downloaded.

## Positioning

Local-first voice cloning with the user's own audio, without sending reference recordings to a hosted service by default.

## Operating Context

The user runs the project on Windows, starts a local backend and frontend, places a reference recording under `data/reference/` when desired, and may use either CUDA or CPU inference. The first model load can download a large checkpoint and can take several minutes.

## Capabilities and Constraints

- Thai zero-shot synthesis uses the existing F5-TTS-THAI service.
- Reference audio must be 2–15 seconds, with 4–8 seconds recommended.
- Supported input formats are WAV, MP3, M4A, FLAC, and browser-recorded WebM.
- The user can record from the browser microphone, preview the reference, and request local Thai transcription before editing the transcript.
- Generated text is limited to 500 characters.
- Output is a 24 kHz WAV file.
- The project must remain local-only by default and must not imply that generated speech is authentic evidence of a person's words.
- Fine-tuning and streaming are explicitly out of scope for this surface; local transcription is included as an assisted zero-shot workflow.

## Brand Commitments

The name is ด็อปเปิลเก็งเงอร์ (Doppelgänger). Copy is Thai-first, direct, calm, and transparent about consent and generated audio.

## Evidence on Hand

The repository contains the working Python synthesis service and setup scripts. No user reference recording has been supplied yet; the UI must explain where to provide one without inventing an example voice.

## Product Principles

- Private by default.
- Make the next action obvious.
- Show what the system is doing while a model is loading or generating.
- Treat generated audio as an artifact to inspect, not proof of a real statement.

## Accessibility & Inclusion

Use labelled controls, keyboard-visible focus, readable Thai typography, sufficient contrast, reduced-motion support, and inline error recovery.
