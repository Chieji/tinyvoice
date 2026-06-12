# TinyVoice

TinyVoice is a beginner-friendly Android/Termux voice assistant prototype. It runs a small Flask service in Termux, serves a localhost side-panel UI, records or uploads speech in the browser, transcribes with a local Whisper model, previews the matched intent, and runs only approved terminal commands after confirmation.

## Safety model

TinyVoice treats every transcript as untrusted input.

- It never executes raw speech text.
- It maps known phrases to predefined argv arrays.
- It does not use shell command strings.
- It requires confirmation before running from the UI.
- It captures stdout/stderr, enforces a timeout, and writes an audit log.
- Unknown or unsafe requests are rejected visibly.

Initial allowlisted phrases:

- `list files` → `ls -la`
- `show disk usage` → `df -h`
- `show current folder` → `pwd`
- `show date` → `date`
- `show who am i` → `whoami`

## Android / Termux setup

Install Termux from F-Droid, then clone this repo and run:

```bash
cd tinyvoice
./scripts/setup-termux.sh
. .venv/bin/activate
python -m tinyvoice
```

Open this URL on the same Android device:

```text
http://127.0.0.1:8765
```

The first launch shows that the Whisper model is not ready. Tap **Download speech model** before transcribing. The default model is `tiny` to keep the prototype realistic on phones. You can choose another model before launch:

```bash
export TINYVOICE_WHISPER_MODEL=base
python -m tinyvoice
```

Runtime data is stored in `~/.tinyvoice` by default. Override it with:

```bash
export TINYVOICE_DATA_DIR=/path/to/data
```

## Incremental test checklist

1. Start the server with `python -m tinyvoice`.
2. Open `http://127.0.0.1:8765` and confirm the side-panel UI loads.
3. Confirm the setup card shows the model as needing download.
4. Tap **Download speech model** and wait for the ready state.
5. Test text-only intent preview by typing `list files` and tapping **Preview action**.
6. Tap **Confirm + run** and confirm command output plus audit entries appear.
7. Record a short phrase or upload a WAV/WebM file.
8. Confirm the transcript appears before you run anything.
9. Try an unsafe phrase such as `delete everything` and confirm it is rejected.

## Troubleshooting

- **`openai-whisper` missing**: activate the virtual environment and run `python -m pip install -r requirements.txt`.
- **`ffmpeg` missing**: run `pkg install ffmpeg` in Termux.
- **Microphone blocked**: grant microphone permission to the browser. If recording still fails, use the file picker with an audio recording.
- **Download interrupted**: tap **Download speech model** again. TinyVoice writes its ready marker only after the backend loads the model successfully.
- **Slow transcription**: keep `TINYVOICE_WHISPER_MODEL=tiny` until the full loop works on your phone.
- **Reset model state**: delete `~/.tinyvoice/models/whisper-tiny.ready` and restart.

## Local development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m tinyvoice
```

Useful smoke check without starting a server:

```bash
python -c "from tinyvoice import create_app; app=create_app(); print(app.url_map)"
```

## Project layout

```text
tinyvoice/
  app.py              Flask API and static UI routes
  commands.py         Allowlisted intent mapping, execution, and audit logging
  config.py           Runtime path and environment configuration
  whisper_local.py    Optional local Whisper integration
  static/             Side-panel browser UI
tests/                Unit and API tests
scripts/              Termux setup and run helpers
tasks/                Plan, verification notes, and lessons
```
