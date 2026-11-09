---
name: "ด็อปเปิลเก็งเงอร์ (Doppelgänger)"
description: "A local Thai voice studio in flat plum, where electric lime marks what you can do and what has played."
colors:
  accent: "#d8f34e"
  accent-hover: "#e6fb7a"
  on-accent: "#1f2600"
  accent-text: "#5b6b00"
  accent-text-dark: "#d8f34e"
  plum: "#33203f"
  on-plum: "#f8f2fa"
  plum-ink-soft: "#cfc3d6"
  plum-line: "#4d3a59"
  record: "#c81e4a"
  record-dark: "#ff7f96"
  ground: "#f4f0f6"
  ground-dark: "#1a1220"
  panel: "#ffffff"
  panel-dark: "#281b30"
  field: "#f1ecf4"
  field-dark: "#35263e"
  line: "#ddd4e2"
  line-dark: "#43324d"
  line-strong: "#8c7d96"
  line-strong-dark: "#86748f"
  ink: "#1f1426"
  ink-dark: "#f8f2fa"
  ink-soft: "#5c4f66"
  ink-soft-dark: "#c0b2c8"
  ink-faint: "#6b5d75"
  ink-faint-dark: "#ad9eb6"
  focus: "#1f1426"
  focus-dark: "#ffffff"
  disabled: "#e2dae7"
  disabled-dark: "#3a2b44"
  track-lane: "#100a14"
  track-bar: "#a99bb2"
typography:
  headline:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.35
  headline-wide:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.35
  title:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.35
  emphasis:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
  body:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  body-small:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
  caption:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  button:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
  mark:
    fontFamily: "Anuphan, Noto Sans Thai, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
rounded:
  mark: "4px"
  field: "6px"
  base: "8px"
  play: "10px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  xxl: "24px"
  gutter: "max(16px, env(safe-area-inset-left), env(safe-area-inset-right))"
components:
  topbar:
    backgroundColor: "{colors.plum}"
    textColor: "{colors.on-plum}"
  brand-mark:
    backgroundColor: "{colors.on-plum}"
    textColor: "{colors.plum}"
    rounded: "{rounded.base}"
    size: "32px"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    typography: "{typography.emphasis}"
    rounded: "{rounded.base}"
    padding: "0 40px"
    height: "52px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.on-accent}"
  button-primary-disabled:
    backgroundColor: "{colors.disabled}"
    textColor: "{colors.ink-faint}"
  button-outline:
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.base}"
    padding: "8px 20px"
    height: "44px"
  button-outline-recording:
    textColor: "{colors.record}"
    typography: "{typography.button}"
    rounded: "{rounded.base}"
    padding: "8px 20px"
    height: "44px"
  button-text:
    textColor: "{colors.accent-text}"
    rounded: "{rounded.base}"
    padding: "0 8px"
    height: "44px"
  button-icon:
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.base}"
    size: "44px"
  button-icon-hover:
    textColor: "{colors.record}"
  button-play:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.play}"
    size: "48px"
  button-play-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.on-accent}"
  button-download:
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.base}"
    height: "44px"
  input-field:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "8px 12px"
  select-field:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "0 40px 0 12px"
    height: "44px"
  step-panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.base}"
    padding: "24px"
  step-mark:
    textColor: "{colors.ink-soft}"
    typography: "{typography.mark}"
    rounded: "{rounded.base}"
    size: "32px"
  step-mark-done:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.base}"
    size: "32px"
  take-track:
    backgroundColor: "{colors.track-lane}"
    rounded: "{rounded.field}"
    height: "72px"
  take-track-result:
    backgroundColor: "{colors.track-lane}"
    rounded: "{rounded.field}"
    height: "112px"
  result-panel:
    backgroundColor: "{colors.plum}"
    textColor: "{colors.on-plum}"
    rounded: "{rounded.base}"
    padding: "24px"
  synthetic-mark:
    textColor: "{colors.on-plum}"
    typography: "{typography.mark}"
    rounded: "{rounded.mark}"
    padding: "0 8px"
---

# Design System: ด็อปเปิลเก็งเงอร์ (Doppelgänger)

## Overview

**Creative North Star: "The Lit Take"**

A voice tool with its own night-studio identity: flat plum surfaces where one electric lime marks what the user can do and what has already played. Three numbered steps carry the work from a source voice to a take the user can inspect, and each step reports its own readiness through a single mark. The system refuses the graphite console, the white form page and any streaming-player likeness.

The system is one column of plain panels under a plum header, with one plum result panel. Density is that of a working tool, compact gaps and full-width controls on a phone, with the result moving to a sticky right column on a wide window. Theme follows the operating system. In a light theme the ground turns pale lilac so white panels separate by tone alone, while the header, the result panel and every track keep their dark treatment, because those surfaces belong to the studio and to the audio.

Trust is part of the visual system. Generated audio always appears with a bordered synthetic mark and a plain consent line, and a waveform is only ever drawn from decoded audio.

**Key Characteristics:**
- Plum header and result panel in both themes, with plum-leaning neutrals everywhere else.
- One electric lime, spent on actions, ready state and played audio.
- Flat solid fills throughout, with no gradients and no shadows.
- Gently squared 8px controls, a 10px play button, and outlined secondary actions.
- A dark take track that is both the waveform and the seek control.
- Thai-first Anuphan alone, with hierarchy from weight and size.

## Colors

Plum-leaning neutrals and a fixed plum surface, with one saturated lime for what can be done or heard, and one red for recording and failure.

Base token names carry the light-theme value. A `-dark` sibling replaces its base under `prefers-color-scheme: dark`. Tokens with no sibling hold in both themes.

### Primary
- **Electric Lime** (#d8f34e): the generate action, the play button, a completed step mark, and played waveform bars, with text selection as its one incidental use.
- **Lime Lifted** (#e6fb7a): hover on the two filled lime controls only.
- **Ink on Lime** (#1f2600): text and icons on any lime fill.
- **Legible Lime** (#5b6b00 light, #d8f34e dark): lime as foreground on panels, for text buttons, the range control, the drag-over outline and the text caret. Light panels cannot carry Electric Lime as text.

### Secondary
- **Studio Plum** (#33203f): the header and the result panel in both themes, and the browser theme color. It is also the icon color inside the brand mark.
- **On Plum** (#f8f2fa): text on plum and the brand mark's plate.
- **Plum Soft Ink** (#cfc3d6): secondary text inside the result panel.
- **Plum Line** (#4d3a59): the divider above the disclaimer in the result panel.

### Tertiary
- **Take Red** (#c81e4a light, #ff7f96 dark): the recording state, errors, an invalid take length, the character limit, and hover on the delete control. The result panel uses the dark value in both themes.

### Neutral
- **Ground** (#f4f0f6 light, #1a1220 dark): the page, and the sticky action bar that must mask content scrolling beneath it.
- **Panel** (#ffffff light, #281b30 dark): step panels.
- **Field** (#f1ecf4 light, #35263e dark): textareas and selects, filled rather than outlined.
- **Line** (#ddd4e2 light, #43324d dark): the divider above the voice settings and the top edge of the action bar.
- **Line Strong** (#8c7d96 light, #86748f dark): outline and download button borders, and field hover borders.
- **Ink** (#1f1426 light, #f8f2fa dark): primary text. **Ink Soft** (#5c4f66 light, #c0b2c8 dark): help, captions, timers, resting icons. **Ink Faint** (#6b5d75 light, #ad9eb6 dark): placeholders and disabled action text.
- **Focus** (#1f1426 light, #ffffff dark): the keyboard outline. The header and the result panel hold it at white in both themes.
- **Disabled** (#e2dae7 light, #3a2b44 dark): the fill of the unavailable primary action.
- **Lane** (#100a14) and **Bar Lilac** (#a99bb2): the take track and its unplayed bars, fixed in both themes.

### Named Rules
**The Lime Earns It Rule.** Electric Lime marks only something the user can act on, something ready, or audio already played. It never marks the brand, a heading or an ornament. The brand mark is plum on On Plum.

**The Plum Stage Rule.** The header and the result panel are Studio Plum and every take track is Lane in both themes, and the result panel locks its own text, focus and accent values to their on-plum forms.

## Typography

**Display Font:** Anuphan (with Noto Sans Thai, Segoe UI, sans-serif)
**Body Font:** Anuphan (with Noto Sans Thai, Segoe UI, sans-serif)

**Character:** A single contemporary Thai family, self-hosted at 400, 500, 600 and 700, with no font synthesis. Semibold headings against calm body text do the hierarchy work, and 700 is kept for the primary action and for marks.

### Hierarchy
- **Headline** (600, 1.5rem rising to 2rem at 720px, 1.35): the task as the page's only h1, balanced across lines.
- **Title** (600, 1.25rem, 1.35): step headings, and nothing else.
- **Emphasis** (700, 1.125rem): the generate action and the empty-state statement.
- **Body** (400, 1rem, 1.6): running text. Textareas open to 1.7 for Thai stacked marks. Empty-state copy holds to 42ch.
- **Body Small** (0.9375rem, 1.5): error messages at 500, warnings at 400, and text buttons at 600.
- **Label** (600, 1rem): field labels, settings summary and filenames.
- **Button** (600, 1rem): outline, text, icon and download controls.
- **Mark** (700, 1rem): the brand name, step numbers and the synthetic mark.
- **Caption** (400, 0.875rem, 1.6): help, counters and timers.

### Named Rules
**The Tall Thai Rule.** No heading goes below a 1.35 line height and no body copy below 1.5, so Thai tone marks and vowels above and below the line never collide.

**The Counting Numerals Rule.** Anything that counts, times or measures uses tabular numerals, so values change in place without the layout shifting.

## Layout

A single centered shell up to 1240px wide, inset by a gutter of at least 16px that also respects device safe areas. Panels stack with 12px gaps on narrow windows and 16px gaps at 1024px and up. Spacing moves in 4, 8, 12, 16, 20 and 24px steps, with a 6px gap only between a label and its field.

Under 560px, panels use 20px by 16px padding and capture actions stack at full width. From 560px, panels pad 24px, capture actions and voice settings sit in two columns, and the generate button sizes to its label instead of filling the row. From 720px the headline grows.

From 1024px the workbench splits into a flexible input column and a 360 to 420px result column, and the result panel sticks 16px from the top with its own scroll. The generate action sticks to the bottom of the viewport inside the input column, masked by the ground color, and un-sticks on windows under 520px tall so it cannot cover the form. Drag-and-drop instructions appear only on devices with a fine hovering pointer.

## Elevation & Depth

Depth comes from tone: ground, then panel, then field, with plum as the one surface that stands apart. The system has no shadows and no gradients, in either theme. Under 1024px the full-bleed sticky action bar separates from content passing beneath it with a 1px Line top edge and its opaque Ground fill. At 1024px and up it drops the edge and relies on the fill alone.

### Named Rules
**The Flat Fill Rule.** Every surface is one solid color. Nothing fades, glows or lifts.

**The Tone Not Line Rule.** Panels separate from the page by value alone. If two panels do not separate, fix the ground, and do not add a border.

## Shapes

One gently squared family, stepped by job. Controls, panels, step marks and the brand mark sit at 8px. The play button alone goes to 10px, as the one transport control. Fields and tracks tighten to 6px, and the synthetic mark to 4px. Nothing in the system is rounded further than the play button.

## Components

Controls are plain and confident, with filled lime kept for generating and playing, and every secondary action outlined or bare.

All state transitions run 180ms ease-out and change color only, so controls do not grow or move on hover. Playback position and the recording fill move 250ms linear, matched to the update tick. Under reduced motion every transition and animation collapses to effectively nothing, and loading is still announced by its text.

### Buttons
- **Shape:** gently squared (8px) with a 44px minimum height, weight 600, with an 18px icon and 8px gap.
- **Primary:** the single generate action, filled Electric Lime with Ink on Lime text, 52px tall, padded 40px, weight 700 at 1.125rem, hovering to Lime Lifted. Unavailable, it fills Disabled with Ink Faint text, and a line above it says what is missing.
- **Outline:** capture actions, transparent with a 1px Line Strong border that darkens to Ink on hover. While recording, border and text turn Take Red at 2px and the label gains a running timer.
- **Text:** Legible Lime with no fill, underlined on hover, used for the transcription helper at 0.9375rem.
- **Icon:** a 44px borderless control in Ink Soft that turns Take Red on hover, used for delete, always with an accessible label.
- **Download:** a full-width outlined action on the plum result panel, transparent with a 1px Line Strong border that lightens to the panel's text color on hover. It stays outlined so that Electric Lime keeps pointing at generate and play.
- **Focus:** every control takes a 3px solid outline in Focus with a 2px offset.
- **Disabled:** non-primary controls drop to 0.6 opacity with a not-allowed cursor.

### Chips
- **Synthetic mark:** bold text in a 2px current-color border with 4px corners. It sits directly under every generated take.

### Cards / Containers
- **Step panel:** 8px corners, Panel fill, no border or shadow, 20 by 16px padding rising to 24px at 560px.
- **Result panel:** the same shape, filled flat Studio Plum in both themes, sticky at 1024px and up, with a 480px minimum height there, or less on a shorter window, so the empty state holds its place.

### Inputs / Fields
- **Style:** Field fill with a 1px transparent border and 6px corners, labelled above with a 600-weight visible label and optional help text below. The main text field is the one exception, named by its step heading on screen and by a screen-reader label.
- **Hover / Focus:** border becomes Line Strong on hover, and focus uses the shared 3px outline.
- **Select:** a native select at 44px minimum height with an overlaid chevron.
- **Range:** a native range at 44px minimum height, accented in Legible Lime, with its value shown in the label.
- **Error:** inline above the action in Take Red with an icon, stating the next step. Length and character-limit problems turn their own caption Take Red at weight 600.

### Navigation
There is no navigation system. The flat plum header holds only a 44px home link with a 32px mark in 8px corners, above the task headline.

### Step Mark
A 32px gently squared tile (8px) with a 2px current-color border and a tabular step number. Once its step is complete the tile fills Electric Lime and the number becomes a check. A screen-reader-only phrase states the same readiness, so the state is never carried by color alone.

### Take Track
The signature component: a Lane-colored track, 72px tall for the source voice and 112px for the result. Bars are drawn only from the decoded peaks of real audio, in Bar Lilac, and turn Electric Lime as they are played. A white 2px playhead marks position, and a transparent native range input laid over the waveform provides seeking and keyboard control, with the focus outline drawn on the lane.

The source lane is scaled to a fixed 15 seconds, shows the recommended 4 to 8 second zone as a faint white band, and sits above a tabular ruler. A recording shows a translucent red elapsed fill with a solid leading edge, never invented bars. With no audio the lane stays empty. If audio cannot be decoded, the lane stays empty and native audio controls take over.

Below it, a 48px lime play button with 10px corners sits beside a tabular time readout. Starting one take pauses any other.

### Named Rules
**The Real Signal Rule.** A bar exists only because a decoded sample produced it. Loading, recording, empty and failed states show no waveform shapes.

**The User Starts Sound Rule.** Audio plays only from a user's press on a play control. Nothing autoplays, including a newly finished take.

**The Marked Take Rule.** A generated take always carries the synthetic mark, and the result panel always carries the line about consent and not passing the audio off as someone's real words.

## Do's and Don'ts

### Do:
- **Do** give every control a visible or programmatic label, and pair every icon-only control with an accessible name.
- **Do** keep every interactive target at least 44px in both dimensions, with 48px for playback and 52px tall for the primary action.
- **Do** honor `prefers-reduced-motion` for every transition, animation and smooth scroll, and keep a text equivalent for anything an animation communicates.
- **Do** keep every surface a single flat fill.
- **Do** use the 3px Focus outline with a 2px offset for keyboard focus on every interactive element.
- **Do** use Legible Lime rather than Electric Lime for lime text on light surfaces.
- **Do** state what is missing beside a disabled primary action.

### Don't:
- **Don't** draw waveform bars from anything but decoded audio, and don't add placeholder or decorative waveforms.
- **Don't** autoplay audio.
- **Don't** present generated speech as authentic, or show a generated take without the synthetic mark.
- **Don't** use Electric Lime for brand marks, headings or decoration.
- **Don't** use gradients on any surface.
- **Don't** add borders or shadows to panels.
- **Don't** render the header, the result panel or a take track in a light treatment, even in the light theme.
- **Don't** use a third-party logo, name or artwork as this product's identity.
- **Don't** round any control past the play button's 10px.
