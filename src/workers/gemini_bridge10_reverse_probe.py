from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

MODEL = os.getenv("GEMINI_VIDEO_MODEL", "gemini-3.6-flash")

IMAGE_DIR = PROJECT_ROOT / "output" / "evidence_test" / "bridge10_control"
OUTPUT_PATH = PROJECT_ROOT / "logs" / "gemini_bridge10_reverse_probe.json"

KEYS = [
    ("BACKUP", os.getenv("GEMINI_API_KEY_BACKUP")),
    ("PRIMARY", os.getenv("GEMINI_API_KEY_PRIMARY")),
]

PROMPT = """
You are evaluating a chess move ambiguity from a sequence of board images.

IMPORTANT:
- These images are in chronological order.
- The board is shown from BLACK'S perspective.
- This means the board is rotated 180 degrees compared with standard White view.
- Use standard chess coordinates.
- Focus only on the FIRST white rook move.

Known candidate paths:

Candidate A:
1. White rook moves e1 -> e5
2. Black rook moves e8 -> e5
3. White rook moves d5 -> e5

Candidate B:
1. White rook moves d5 -> e5
2. Black rook moves e8 -> e5
3. White rook moves e1 -> e5

TASK:
Decide which candidate is visually better supported by the image sequence.

Rules:
- Do NOT invent another line.
- Do NOT use strategic reasoning.
- Judge only from the chronological images.
- If uncertain, choose the better-supported candidate and lower confidence.
- Return raw JSON only.

Return:
{
  "selected_candidate": "A or B",
  "selected_first_source": "d5 or e1",
  "selected_first_destination": "e5",
  "confidence": "high or medium or low",
  "earliest_departure_frame": "frame identifier",
  "latest_confirmation_frame": "frame identifier",
  "visual_reasoning": [
    "short observation 1",
    "short observation 2",
    "short observation 3"
  ]
}
"""


def extract_json(text: str) -> dict:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response.")

    return json.loads(cleaned[start:end + 1])


def run_with_key(key_name: str, api_key: str, image_paths: list[Path]) -> dict:
    client = genai.Client(api_key=api_key)

    try:
        uploaded_images = []
        for path in image_paths:
            uploaded = client.files.upload(file=path)
            uploaded_images.append(uploaded)

        contents = [*uploaded_images, PROMPT]

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
        )

        parsed = extract_json(response.text or "")

        return {
            "key_used": key_name,
            "model": MODEL,
            "image_paths": [str(p) for p in image_paths],
            "result": parsed,
            "raw_text": response.text,
        }

    finally:
        client.close()


def main() -> int:
    image_paths = sorted(IMAGE_DIR.glob("*.jpg"))

    if len(image_paths) != 7:
        raise RuntimeError(
            f"Expected 7 images in {IMAGE_DIR}, found {len(image_paths)}"
        )

    failures = []
    output = None

    for key_name, api_key in KEYS:
        if not api_key:
            continue

        try:
            print(f"=== TRYING {key_name} KEY ===")
            output = run_with_key(key_name, api_key, image_paths)
            break
        except Exception as exc:
            failures.append({
                "key": key_name,
                "error_type": type(exc).__name__,
                "error": str(exc)[:500],
            })
            print(f"{key_name} failed: {type(exc).__name__}: {exc}")

    if output is None:
        print("ERROR: all Gemini keys failed.")
        print(json.dumps(failures, indent=2))
        return 1

    output["failed_attempts"] = failures

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    result = output["result"]

    print()
    print("=== BRIDGE 10 REVERSE PROBE RESULT ===")
    print("Key used                :", output["key_used"])
    print("Model                   :", output["model"])
    print("Selected candidate      :", result.get("selected_candidate"))
    print("Selected first source   :", result.get("selected_first_source"))
    print("Selected destination    :", result.get("selected_first_destination"))
    print("Confidence              :", result.get("confidence"))
    print("Earliest departure frame:", result.get("earliest_departure_frame"))
    print("Latest confirm frame    :", result.get("latest_confirmation_frame"))
    print("Visual reasoning:")
    for item in result.get("visual_reasoning", []):
        print("-", item)

    print()
    print("Saved:", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
