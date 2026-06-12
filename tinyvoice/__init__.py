"""TinyVoice: a local-first Termux voice assistant prototype."""


def create_app(*args, **kwargs):
    """Create the Flask app lazily so non-web helpers remain importable."""

    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app"]
