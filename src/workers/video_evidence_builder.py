from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2


SAMPLE_FPS = 12.0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create dense timestamped chess-board evidence frames."
    )

    parser.add_argument(
        "video",
        type=Path,
        help="Board-only video clip.",
    )

    parser.add_argument(
        "--original-start",
        type=float,
        default=13.50,
        help="Timestamp of this clip inside the original recording.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/evidence_test/dense_frames"),
    )

    args = parser.parse_args()

    video_path = args.video.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    if not video_path.is_file():
        raise SystemExit(f"Video not found: {video_path}")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    cap = cv2.VideoCapture(
        str(video_path)
    )

    source_fps = float(
        cap.get(
            cv2.CAP_PROP_FPS
        )
    )

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    if source_fps <= 0:
        raise SystemExit(
            "Could not determine source FPS."
        )

    duration = (
        frame_count
        / source_fps
    )

    sample_interval = (
        1.0
        / SAMPLE_FPS
    )

    evidence = []

    sample_number = 0
    relative_time = 0.0

    while relative_time < duration:

        cap.set(
            cv2.CAP_PROP_POS_MSEC,
            relative_time * 1000.0,
        )

        ok, frame = cap.read()

        if not ok:
            break

        original_time = (
            args.original_start
            + relative_time
        )

        filename = (
            f"frame_{sample_number:03d}"
            f"_t{original_time:07.3f}.jpg"
        )

        output_path = (
            output_dir
            / filename
        )

        cv2.imwrite(
            str(output_path),
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                95,
            ],
        )

        evidence.append(
            {
                "index": sample_number,
                "file": filename,
                "relative_time": round(
                    relative_time,
                    4,
                ),
                "original_time": round(
                    original_time,
                    4,
                ),
            }
        )

        sample_number += 1
        relative_time += (
            sample_interval
        )

    cap.release()

    manifest = {
        "source_video": str(
            video_path
        ),
        "source_fps": source_fps,
        "duration": duration,
        "sample_fps": SAMPLE_FPS,
        "original_start": (
            args.original_start
        ),
        "frame_count": len(
            evidence
        ),
        "frames": evidence,
    }

    manifest_path = (
        output_dir
        / "manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "=== VIDEO EVIDENCE BUILDER ==="
    )
    print(
        f"Source FPS      : "
        f"{source_fps:.2f}"
    )
    print(
        f"Duration        : "
        f"{duration:.2f}s"
    )
    print(
        f"Evidence FPS    : "
        f"{SAMPLE_FPS:.2f}"
    )
    print(
        f"Frames exported : "
        f"{len(evidence)}"
    )
    print(
        f"Output          : "
        f"{output_dir}"
    )
    print(
        f"Manifest        : "
        f"{manifest_path}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
