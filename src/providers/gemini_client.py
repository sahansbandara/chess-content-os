from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class GeminiFallbackClient:
    def __init__(self) -> None:
        self.model = os.getenv(
            "GEMINI_VIDEO_MODEL",
            "gemini-3.6-flash",
        )

        # Backup is currently the verified-working key,
        # so try it first.
        self.keys = [
            (
                "BACKUP",
                os.getenv(
                    "GEMINI_API_KEY_BACKUP"
                ),
            ),
            (
                "PRIMARY",
                os.getenv(
                    "GEMINI_API_KEY_PRIMARY"
                ),
            ),
        ]

        self.keys = [
            (name, key)
            for name, key in self.keys
            if key
        ]

        if not self.keys:
            raise RuntimeError(
                "No Gemini API keys configured."
            )

    def generate_content(
        self,
        contents,
        config=None,
    ):
        failures = []

        for key_name, api_key in self.keys:
            client = genai.Client(
                api_key=api_key
            )

            try:
                response = (
                    client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    )
                )

                return {
                    "response": response,
                    "key_used": key_name,
                    "model": self.model,
                }

            except Exception as exc:
                failures.append(
                    (
                        key_name,
                        type(exc).__name__,
                        str(exc)[:300],
                    )
                )

            finally:
                client.close()

        details = " | ".join(
            f"{name}: {error_type}"
            for (
                name,
                error_type,
                _message,
            ) in failures
        )

        raise RuntimeError(
            "All Gemini keys failed: "
            + details
        )
