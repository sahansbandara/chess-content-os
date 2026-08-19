"""Reconstruct a legal move sequence from an observed board-state sequence.

Walks the observed states in order. For each one, searches for the shortest
legal path from the current board that reaches it. States no short legal path
can reach are treated as animation transients (a piece mid-flight reads as
missing) and skipped — never forced into the game.

Ambiguity is reported, not resolved: when more than one shortest path reaches a
state, every candidate is recorded and the bridge is flagged. Picking the first
one silently is exactly what this project forbids.

Run:
  uv run python src/workers/reconstruct_from_states.py logs/early_window_scan.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess

MAX_PLIES = 3       # per bridge; deeper searches explode and mean the scan is too sparse
MAX_CANDIDATES = 8  # stop enumerating once a bridge is clearly ambiguous


def paths_to(board, target_fen, max_plies=MAX_PLIES, limit=MAX_CANDIDATES):
    """All shortest legal move paths from `board` reaching `target_fen`."""
    if board.board_fen() == target_fen:
        return [[]]

    frontier = [(board.copy(stack=False), [])]
    for _ in range(max_plies):
        found, nxt = [], []
        for state, path in frontier:
            for move in state.legal_moves:
                child = state.copy(stack=False)
                child.push(move)
                step = path + [move]
                if child.board_fen() == target_fen:
                    found.append(step)
                    if len(found) >= limit:
                        return found
                else:
                    nxt.append((child, step))
        if found:
            return found
        frontier = nxt
    return []


def reconstruct(runs, start_fen=None, side_to_move=chess.WHITE):
    board = chess.Board(None)
    board.set_board_fen(start_fen or runs[0]["board_fen"])
    board.turn = side_to_move

    moves, bridges, skipped = [], [], []

    for i, run in enumerate(runs):
        target = run["board_fen"]
        if board.board_fen() == target:
            continue

        candidates = paths_to(board, target)
        if not candidates:
            skipped.append({"index": i, "t_start": run["t_start"], "board_fen": target})
            continue

        chosen = candidates[0]
        ambiguous = len(candidates) > 1

        bridges.append(
            {
                "to_state_index": i,
                "t_start": run["t_start"],
                "plies": len(chosen),
                "candidates": len(candidates),
                "ambiguous": ambiguous,
                "candidate_sans": [
                    " ".join(_san_line(board, c)) for c in candidates[:MAX_CANDIDATES]
                ] if ambiguous else None,
            }
        )

        for mv in chosen:
            moves.append(
                {
                    "ply": len(moves) + 1,
                    "uci": mv.uci(),
                    "san": board.san(mv),
                    "side": "w" if board.turn == chess.WHITE else "b",
                    "t_observed": run["t_start"],
                    "bridge_index": len(bridges) - 1,
                    "ambiguous_bridge": ambiguous,
                }
            )
            board.push(mv)

    return moves, bridges, skipped, board


def _san_line(board, path):
    b = board.copy(stack=False)
    out = []
    for mv in path:
        out.append(b.san(mv))
        b.push(mv)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scan", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    runs = json.loads(args.scan.read_text())["runs"]
    moves, bridges, skipped, final = reconstruct(runs)

    ambiguous = [b for b in bridges if b["ambiguous"]]
    print(f"{len(runs)} observed states -> {len(moves)} plies")
    print(f"{len(bridges)} bridges, {len(ambiguous)} ambiguous, {len(skipped)} states skipped as transients\n")

    line = []
    for m in moves:
        if m["side"] == "w":
            line.append(f"{(m['ply']+1)//2}. {m['san']}")
        else:
            line.append(m["san"])
    print(" ".join(line))

    if skipped:
        print("\nskipped (no short legal path — animation transients):")
        for s in skipped:
            print(f"  t={s['t_start']:>6.2f}  {s['board_fen']}")

    if ambiguous:
        print("\nAMBIGUOUS bridges — must not be silently resolved:")
        for b in ambiguous:
            print(f"  t={b['t_start']:>6.2f}  {b['candidates']} candidates: {b['candidate_sans']}")

    print(f"\nfinal position: {final.board_fen()}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps({"moves": moves, "bridges": bridges, "skipped": skipped,
                        "final_board_fen": final.board_fen()}, indent=2) + "\n"
        )
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
