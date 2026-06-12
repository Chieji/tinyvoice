# Termux Voice Assistant v1 Plan

## Goal
Build a beginner-friendly Android/Termux prototype that serves a localhost side-panel UI, supports explicit first-run Whisper model setup, records/transcribes speech locally when platform tools are available, maps transcripts to allowlisted commands, and safely executes only approved terminal tasks after visible review.

## Checkable steps

- [x] Step 1: Scaffold the app package and documented entry points.
  - Acceptance criteria: repository contains a Python package, Flask app entry point, static UI assets, dependency file, setup/run helper scripts, and README usage instructions for Termux.
  - Known failure modes: missing dependency declarations or scripts not executable; handle by validating import paths and script execution in tests.
  - Verification: run unit tests and a smoke import of the Flask app.

- [x] Step 2: Implement safe command intent mapping and execution.
  - Acceptance criteria: raw transcripts are never passed to a shell; known phrases map to allowlisted argv arrays; unknown commands are rejected; execution uses timeout, fixed working directory, captured output, and audit logging.
  - Known failure modes: accidental shell=True, weak matching, dangerous command expansion; handle with code review and tests for rejected requests.
  - Verification: unit tests for allowed commands, rejected commands, dry-run/preview behavior, audit log creation, and timeout-safe subprocess call boundaries.

- [x] Step 3: Implement Whisper model status/download/transcription services.
  - Acceptance criteria: first-run status is visible; download is explicit and writes a marker only after verification; transcription works through a local backend when installed and returns clear setup errors otherwise.
  - Known failure modes: network or platform package unavailable in CI, partial download marker, heavyweight model download during tests; handle by making downloads opt-in, mocking in tests, and keeping fallback errors actionable.
  - Verification: unit tests with mocked downloader/transcriber and smoke API tests.

- [x] Step 4: Implement microphone/audio API and side-panel browser UI.
  - Acceptance criteria: UI shows setup status, model controls, record/stop/upload path, transcript, proposed action, execution result, and audit trail; API accepts uploaded audio and returns transcription/intent preview.
  - Known failure modes: browser microphone unavailable on Android localhost, unsupported audio MIME types, missing ffmpeg; handle by supporting browser MediaRecorder upload and documenting Termux/ffmpeg prerequisites.
  - Verification: Flask test client checks all endpoints and static page availability; manual static asset inspection.

- [x] Step 5: Add project tests, documentation, and final task capture.
  - Acceptance criteria: pytest suite covers core safety and API behavior; README includes Android/Termux setup, incremental testing checklist, troubleshooting, and safety model; tasks/lessons.md exists with relevant process notes.
  - Known failure modes: tests depend on Android-only binaries or network; handle by isolating platform integrations behind injectable services and mocking them.
  - Verification: run pytest, compile Python files, run Flask app import smoke, update this todo with final test results.

## Verification strategy before implementation

1. Run `python -m compileall tinyvoice tests` to catch syntax/import issues.
2. Run `python -m pytest` for unit and API coverage.
3. Run a Flask import/URL-map smoke command without starting a long-lived server.
4. Review `git diff` for safety properties: no `shell=True`, no raw transcript execution, no automatic model download on import/startup, and no committed generated model/audio artifacts.

## Final acceptance checklist

- [x] Localhost side-panel UI exists and can drive the setup/transcribe/preview/execute loop.
- [x] Whisper setup is explicit and recoverable.
- [x] Command execution is allowlisted, audited, timeout-bound, and confirmation-oriented.
- [x] Tests pass without Android hardware or network for non-Flask core; Flask API tests are included and skip only when Flask is not installed in the environment.
- [x] README explains how to run and test the prototype in Termux.


## Final verification results

- PASS: `python -m compileall tinyvoice tests` completed successfully.
- PASS: `python -m pytest` completed with 7 passed and 1 skipped. The skipped tests are Flask API tests because this container does not have Flask installed and package installation was blocked by the network proxy.
- PASS: `python -c "from tinyvoice import create_app; print(callable(create_app))"` confirmed the package import remains safe even without Flask installed.
- WARNING: `python -c "from tinyvoice.app import create_app; app=create_app(); print(app.url_map)"` could not run in this container because Flask is not installed. The Termux setup script and requirements file install Flask for the actual app runtime.
- PASS: `! rg "shell=True|os\.system|subprocess\.Popen|eval\(|exec\(" tinyvoice tests scripts README.md` found no unsafe shell execution patterns.

## Self-audit notes

- Caught and fixed an import coupling issue: importing `tinyvoice.config` executed `tinyvoice.__init__`, which eagerly imported Flask through `tinyvoice.app`. `tinyvoice.__init__` now exposes `create_app` lazily so core modules and tests remain importable before web dependencies are installed.
- Alternative considered: installing Flask in the container. That was attempted, but pip was blocked by a 403 proxy response, so the implementation keeps Flask as a declared runtime dependency while allowing non-web tests to run without it.
