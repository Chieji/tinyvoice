#!/usr/bin/env bash
set -euo pipefail

pkg update
pkg install -y python ffmpeg git clang make rust libjpeg-turbo
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
python -m pip install -r requirements.txt
termux-setup-storage || true
cat <<'MSG'

Setup complete.
Run: . .venv/bin/activate && python -m tinyvoice
Open: http://127.0.0.1:8765
If Android asks for microphone permission, allow it for your browser.
MSG
