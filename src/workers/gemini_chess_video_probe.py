from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)

VIDEO_PATH = (
    PROJECT_ROOT
    / "output"
    / "evidence_test"
    / "rapid_board_gemini.mp4"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "logs"
    / "gemini_chess_video_probe.json"
)

MODEL = os.getenv(
    "GEMINI_VIDEO_MODEL",
    "gemini-3.6-flash",
)

ORIGINAL_START = 13.50
ANALYSIS_SCALE = 12.0


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


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "moves": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "integer"
                    },
                    "analysis_time_seconds": {
                        "type": "number",
                        "description": (
                            "Approximate timestamp in "
                            "the slowed analysis video "
                            "where the move becomes visible."
                        ),
                    },
                    "side": {
                        "type": "string",
                        "enum": [
                            "white",
                            "black",
                            "uncertain",
                        ],
                    },
                    "piece": {
                        "type": [
                            "string",
                            "null",
                        ],
                    },
                    "from_square": {
                        "type": [
                            "string",
                            "null",
                        ],
                        "description": (
                            "Standard chess coordinate "
                            "such as e2."
                        ),
                    },
                    "to_square": {
                        "type": [
                            "string",
                            "null",
                        ],
                        "description": (
                            "Standard chess coordinate "
                            "such as e4."
                        ),
                    },
                    "capture": {
                        "type": [
                            "boolean",
                            "null",
                        ],
                    },
                    "confidence": {
                        "type": "string",
                        "enum": [
                            "high",
                            "medium",
                            "low",
                        ],
                    },
                    "visual_note": {
                        "type": "string",
                    },
                },
                "required": [
                    "sequence",
                    "analysis_time_seconds",
                    "side",
                    "piece",
                    "from_square",
                    "to_square",
                    "capture",
                    "confidence",
                    "visual_note",
                ],
            },
        },
        "uncertain_events": {
            "type": "array",
            "items": {
                "type": "string"
            },
        },
    },
    "required": [
        "moves",
        "uncertain_events",
    ],
}


PROMPT = """
Analyze this chess-board replay visually.

IMPORTANT VIDEO CONSTRUCTION:
- This is NOT normal-speed gameplay.
- It contains 72 sampled board frames.
- Frames were sampled at 12 frames per second
  from the original gameplay.
- Each sampled frame is then held for about
  one second in this analysis video.
- Analysis video second 0 corresponds to
  original gameplay time 13.50 seconds.

BOARD ORIENTATION:
- The board is shown from Black's perspective.
- The board is rotated 180 degrees.
- Top-left square is h1.
- Top-right square is a1.
- Bottom-left square is h8.
- Bottom-right square is a8.

REFERENCE:
The first visible board has this piece-placement
FEN from a separate local board scanner:

r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R

This is piece placement only, not a complete FEN.

TASK:
Identify the actual chess moves visible through
the video in chronological order.

Use the video pixels as the evidence.

For every move:
1. Identify which piece visibly leaves a square.
2. Identify the square where that same piece
   visibly settles.
3. Give the source and destination using
   standard chess coordinates.
4. Report the approximate timestamp in the
   SLOWED analysis video.
5. Mark confidence high, medium, or low.

RULES:
- Do NOT generate SAN notation.
- Do NOT choose moves because they are
  strategically sensible.
- Do NOT invent a move to complete a sequence.
- Intermediate animation frames may exist.
- Treat intermediate animation as part of a
  move, not as separate chess positions.
- A capture should be reported only when
  visually supported.
- If source or destination cannot be seen
  reliably, use null.
- Preserve uncertain events rather than
  guessing.
- Return every visually supported move you can
  identify, in chronological order.
"""


def wait_until_active(
    client: genai.Client,
    uploaded,
):
    while True:
        state = (
            uploaded.state.name
            if uploaded.state
            else None
        )

        print(
            "File state:",
            state,
        )

        if state == "ACTIVE":
            return uploaded

        if state == "FAILED":
            raise RuntimeError(
                "Gemini file processing failed."
            )

        time.sleep(3)

        uploaded = client.files.get(
            name=uploaded.name
        )


def run_with_key(
    key_name: str,
    api_key: str,
):
    client = genai.Client(
        api_key=api_key
    )

    try:
        print()
        print(
            f"=== TRYING {key_name} KEY ==="
        )

        print(
            "Uploading:",
            VIDEO_PATH,
        )

        uploaded = client.files.upload(
            file=VIDEO_PATH
        )

        uploaded = wait_until_active(
            client,
            uploaded,
        )

        print(
            "Gemini file ACTIVE."
        )

        interaction = (
            client.interactions.create(
                model=MODEL,
                input=[
                    {
                        "type": "video",
                        "uri": uploaded.uri,
                        "mime_type": (
                            uploaded.mime_type
                        ),
                        "resolution": "high",
                    },
                    {
                        "type": "text",
                        "text": PROMPT,
                    },
                ],
                response_format={
                    "type": "text",
                    "mime_type": (
                        "application/json"
                    ),
                    "schema": RESPONSE_SCHEMA,
                },
            )
        )

        parsed = json.loads(
            interaction.output_text
        )

        return parsed

    finally:
        client.close()


def main() -> int:
    if not VIDEO_PATH.is_file():
        print(
            "ERROR: analysis video "
            f"not found: {VIDEO_PATH}"
        )
        return 1

    failures = []

    result = None
    key_used = None

    for key_name, api_key in KEYS:
        if not api_key:
            continue

        try:
            result = run_with_key(
                key_name,
                api_key,
            )

            key_used = key_name
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
                f"{key_name} failed:",
                type(exc).__name__,
            )

    if result is None:
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

    for move in result.get(
        "moves",
        []
    ):
        analysis_time = float(
            move[
                "analysis_time_seconds"
            ]
        )

        move[
            "estimated_original_time"
        ] = round(
            ORIGINAL_START
            + analysis_time
            / ANALYSIS_SCALE,
            4,
        )

    output = {
        "model": MODEL,
        "key_used": key_used,
        "source_video": str(
            VIDEO_PATH
        ),
        "original_start": (
            ORIGINAL_START
        ),
        "analysis_scale": (
            ANALYSIS_SCALE
        ),
        "result": result,
        "failed_attempts": failures,
    }

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

    print()
    print(
        "=== GEMINI CHESS VIDEO RESULT ==="
    )
    print(
        "Key used :",
        key_used,
    )
    print(
        "Model    :",
        MODEL,
    )
    print(
        "Moves    :",
        len(
            result.get(
                "moves",
                [],
            )
        ),
    )

    print()

    for move in result.get(
        "moves",
        []
    ):
        print(
            f"{move['sequence']:02d} | "
            f"{move['side']:9s} | "
            f"{move['piece']} | "
            f"{move['from_square']} -> "
            f"{move['to_square']} | "
            f"analysis="
            f"{move['analysis_time_seconds']:.2f}s | "
            f"original≈"
            f"{move['estimated_original_time']:.3f}s | "
            f"{move['confidence']}"
        )

    print()
    print(
        "Uncertain events:",
        len(
            result.get(
                "uncertain_events",
                [],
            )
        ),
    )

    for event in result.get(
        "uncertain_events",
        []
    ):
        print(
            "-",
            event,
        )

    print()
    print(
        "Saved:",
        OUTPUT_PATH,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
