from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)

MODEL = os.getenv(
    "GEMINI_VIDEO_MODEL",
    "gemini-3.6-flash",
)

IMAGE_DIR = (
    PROJECT_ROOT
    / "output"
    / "evidence_test"
    / "bridge10_control"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "logs"
    / "gemini_bridge10_unlabeled_inline_probe.json"
)

KEYS = [
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


PROMPT = """
You are given seven chronological images of the
same chess board during a short animation.

Board orientation:
- The board is viewed from Black's perspective.
- The board is rotated 180 degrees.

Important:
Two WHITE rooks are relevant.

One starts on d5.
One starts on e1.

Question:
Which white rook visibly LEAVES its starting
square FIRST in this chronological image sequence?

Choose only:
- d5
- e1

Do not use chess strategy.
Do not reconstruct the whole game.
Do not infer from what move would be legal.
Judge only visible temporal evidence.

Return JSON only:

{
  "first_source_square": "d5 or e1",
  "confidence": "high or medium or low",
  "first_visible_change_frame": 1,
  "confirmation_frame": 1,
  "reason": "short visual explanation"
}
"""


def parse_json(text: str) -> dict:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].startswith("```")
        ):
            lines = lines[:-1]

        cleaned = "\n".join(
            lines
        ).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object found."
        )

    return json.loads(
        cleaned[start:end + 1]
    )


def build_contents(
    image_paths: list[Path],
):
    contents = [
        PROMPT,
    ]

    for index, path in enumerate(
        image_paths,
        start=1,
    ):
        contents.append(
            f"Chronological frame {index}:"
        )

        contents.append(
            types.Part.from_bytes(
                data=path.read_bytes(),
                mime_type="image/jpeg",
            )
        )

    return contents


def run_with_key(
    key_name: str,
    api_key: str,
    image_paths: list[Path],
):
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=120_000,
        ),
    )

    try:
        response = (
            client.models.generate_content(
                model=MODEL,
                contents=build_contents(
                    image_paths
                ),
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type=(
                        "application/json"
                    ),
                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    ),
                ),
            )
        )

        parsed = parse_json(
            response.text or ""
        )

        return {
            "key_used": key_name,
            "model": MODEL,
            "result": parsed,
            "raw_text": response.text,
        }

    finally:
        client.close()


def main() -> int:
    image_paths = sorted(
        IMAGE_DIR.glob("*.jpg")
    )

    if len(image_paths) != 7:
        raise RuntimeError(
            "Expected 7 Bridge 10 images, "
            f"found {len(image_paths)}."
        )

    failures = []
    output = None

    for key_name, api_key in KEYS:
        if not api_key:
            continue

        print(
            f"=== TRYING {key_name} KEY ==="
        )

        try:
            output = run_with_key(
                key_name,
                api_key,
                image_paths,
            )
            break

        except Exception as exc:
            failures.append(
                {
                    "key": key_name,
                    "error_type": (
                        type(exc).__name__
                    ),
                    "error": str(exc)[:500],
                }
            )

            print(
                f"{key_name} failed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    if output is None:
        print(
            "ERROR: all Gemini keys failed."
        )
        print(
            json.dumps(
                failures,
                indent=2,
            )
        )
        return 1

    output[
        "failed_attempts"
    ] = failures

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = output["result"]

    print()
    print(
        "=== BRIDGE 10 UNLABELED INLINE RESULT ==="
    )
    print(
        "Key used           :",
        output["key_used"],
    )
    print(
        "Model              :",
        output["model"],
    )
    print(
        "First source square:",
        result.get(
            "first_source_square"
        ),
    )
    print(
        "Confidence         :",
        result.get(
            "confidence"
        ),
    )
    print(
        "First change frame :",
        result.get(
            "first_visible_change_frame"
        ),
    )
    print(
        "Confirmation frame :",
        result.get(
            "confirmation_frame"
        ),
    )
    print(
        "Reason             :",
        result.get(
            "reason"
        ),
    )

    print()
    print(
        "Saved:",
        OUTPUT_PATH,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
