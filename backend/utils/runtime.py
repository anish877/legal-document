from __future__ import annotations

import os


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_PROFILE = os.getenv("APP_PROFILE", "full").strip().lower()
LITE_MODE = APP_PROFILE == "lite"

# Transformer-heavy features are disabled in lite mode unless explicitly re-enabled.
ENABLE_TRANSFORMERS = env_flag("ENABLE_TRANSFORMERS", default=not LITE_MODE)

# OCR is useful but expensive to ship because it needs Tesseract in the image.
ENABLE_OCR = env_flag("ENABLE_OCR", default=not LITE_MODE)
