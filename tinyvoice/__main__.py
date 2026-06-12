"""Run TinyVoice with `python -m tinyvoice`."""

from .app import create_app


create_app().run(host="127.0.0.1", port=8765)
