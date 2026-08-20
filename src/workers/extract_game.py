"""End-to-end move extraction: recording in, verified move list out.

Seven layers, each catching what the one before it cannot:

  1. one ffmpeg pass over the cropped board      ~30x faster than a spawn per sample
  2. dense sampling                              coarse sampling drops moves entirely
  3. per-square majority vote over a window      kills one-frame misreads and transients
  4. drop animation transients                   a piece in flight is on neither square
  5. repair misread pieces from material         a queen read as a rook is legal but wrong
  6. difference-guided bridge search             blind BFS past 3 plies is infeasible
  7. ambiguity reported, never resolved          several legal paths means several, not one

Castling rights are inferred from king and rook placement. A piece-placement FEN
carries none, and without them O-O is not a legal move, so any game where a side
castles cannot be reconstructed at all.

Run:
  uv run python src/workers/extract_game.py <video> --duration 41.4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKERS = Path(__file__).resolve().parent
ROOT = WORKERS.parents[1]
for path in (str(WORKERS), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import chess  # noqa: E402

from dense_board_track import (  # noqa: E402
    DEFAULT_PROFILE, calculate_thresholds, classify_frame, decode_board_frames,
    load_templates, probe_resolution, smooth, to_fen,
)

from src.perception.bridge_search import board_from_placement, find_paths, san_line  # noqa: E402
from src.validators.constrained_reclassify import drop_transient_states, resolve_misread  # noqa: E402
from src.validators.material_sanity import check_material, check_transition  # noqa: E402
from src.validators.review_rewind import split_mainline  # noqa: E402


def observe(video, profile_path, start, end, fps, window, min_hold):
    profile, templates = load_templates(profile_path)
    empty_threshold, color_threshold = calculate_thresholds(templates)
    width, height = probe_resolution(video)
    board_top = round(height * float(profile["board_top_ratio"]))
    square_size = width // 8

    raw = [
        classify_frame(f, profile, templates, empty_threshold, color_threshold, square_size)
        for f in decode_board_frames(video, board_top, width, fps, start, end)
    ]
    fens = [to_fen(f) for f in smooth(raw, window)]

    runs = []
    for i, fen in enumerate(fens):
        t = start + i / fps
        if runs and runs[-1]["board_fen"] == fen:
            runs[-1]["t_end"] = round(t, 3)
            runs[-1]["frames"] += 1
        else:
            runs.append({"t_start": round(t, 3), "t_end": round(t, 3), "board_fen": fen, "frames": 1})
    return [r for r in runs if r["frames"] >= min_hold]


def clean(runs):
    """Drop transients, repair misread pieces, then strip review demonstrations.

    The order matters. A misread piece breaks the placement equality that rewind
    detection depends on, so repairs come first; a demonstration that is left in
    becomes invented plies downstream, so it goes before reconstruction.

    Returns (runs, report).
    """
    runs, dropped = drop_transient_states([dict(r) for r in runs])

    repairs, unresolved = [], []
    for i in range(1, len(runs)):
        if not check_transition(runs[i - 1]["board_fen"], runs[i]["board_fen"]):
            continue
        res = resolve_misread(runs[i - 1]["board_fen"], runs[i]["board_fen"])
        if res and not res.get("ambiguous"):
            runs[i]["board_fen"] = res["corrected_fen"]
            repairs.append({"t": runs[i]["t_start"], **{k: res[k] for k in ("square", "observed", "corrected_to", "reason")}})
        else:
            unresolved.append({"t": runs[i]["t_start"], "detail": res})

    runs, review = split_mainline(runs)

    return runs, {
        "transients_dropped": len(dropped),
        "pieces_repaired": repairs,
        "unresolved": unresolved,
        "review": review,
    }


def reconstruct(runs, max_plies=4):
    board = board_from_placement(runs[0]["board_fen"], "w")
    moves, ambiguous, unreachable = [], [], []

    for r in runs:
        if board.board_fen() == r["board_fen"]:
            continue
        paths = find_paths(board, r["board_fen"], max_plies=max_plies)
        if not paths:
            unreachable.append(r["t_start"])
            continue
        if len(paths) > 1:
            ambiguous.append({"t": r["t_start"], "candidates": [" ".join(san_line(board, p)) for p in paths]})
        for mv in paths[0]:
            moves.append({
                "ply": len(moves) + 1,
                "uci": mv.uci(),
                "san": board.san(mv),
                "side": "w" if board.turn == chess.WHITE else "b",
                "t_observed_s": r["t_start"],
                "ambiguous_bridge": len(paths) > 1,
            })
            board.push(mv)

    return moves, board, {"ambiguous_bridges": ambiguous, "unreachable_states": unreachable}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--window", type=int, default=7)
    ap.add_argument("--min-hold", type=int, default=3)
    ap.add_argument("--max-plies", type=int, default=4)
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    ap.add_argument("--out", type=Path, default=Path("logs/extracted_game.json"))
    args = ap.parse_args()

    video = args.video.expanduser().resolve()
    print(f"observing {args.start}-{args.duration}s @ {args.fps}fps ...")
    runs = observe(video, args.profile.expanduser().resolve(), args.start, args.duration,
                   args.fps, args.window, args.min_hold)
    print(f"  {len(runs)} stable states")

    runs, report = clean(runs)
    print(f"  dropped {report['transients_dropped']} transients, repaired {len(report['pieces_repaired'])} pieces")
    for r in report["pieces_repaired"]:
        print(f"    t={r['t']:.2f} {r['square']}: {r['observed']} -> {r['corrected_to']}")

    review = report["review"]
    print(f"  review: {len(review['rewinds'])} rewinds, "
          f"{len(review['branch_states'])} demonstrated states dropped, "
          f"{len(runs)} states on the played line")
    for r in review["rewinds"]:
        print(f"    t={r['t']:.2f} stepped back to the position first shown at t={r['back_to_t']:.2f}")
    if review["ends_off_mainline"]:
        print("    WARNING: the recording ends inside a demonstration — "
              "the tail of the game was never shown")

    bad = sum(1 for a, b in zip(runs, runs[1:]) if check_transition(a["board_fen"], b["board_fen"]))
    insane = sum(1 for r in runs if check_material(r["board_fen"]))
    print(f"  material: {insane} impossible positions, {bad} impossible transitions")

    moves, final, recon = reconstruct(runs, args.max_plies)
    complete = final.board_fen() == runs[-1]["board_fen"]

    print(f"\n{len(moves)} plies | {len(recon['ambiguous_bridges'])} ambiguous | "
          f"{len(recon['unreachable_states'])} unreachable | complete={complete}\n")

    line = []
    for m in moves:
        line.append(f"{(m['ply'] + 1) // 2}.{m['san']}" if m["side"] == "w" else m["san"])
    print(" ".join(line))

    if recon["ambiguous_bridges"]:
        print("\nAMBIGUOUS — these need human confirmation, they are not resolved:")
        for a in recon["ambiguous_bridges"]:
            print(f"  t={a['t']:.2f}: {a['candidates']}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "video": video.name, "settings": vars(args) | {"video": str(video), "profile": str(args.profile), "out": str(args.out)},
        "complete": complete, "final_board_fen": final.board_fen(),
        "last_observed_fen": runs[-1]["board_fen"],
        "cleaning": report, "reconstruction": recon, "moves": moves,
    }, indent=2, default=str) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
