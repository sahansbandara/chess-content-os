"""Run Stockfish over a verified moves.json and emit analysis.json.

Engine output lives in its own file. It never mutates move truth — moves.json
records what happened, analysis.json records what the engine thinks of it.

Only plies the contract validator accepts are analysed; an unresolved move must
not acquire an engine opinion that later reads as fact.

Run:  uv run python -m src.analysis.analyze_moves
"""

import json
import os
from pathlib import Path

import chess
import chess.engine

from src.analysis.move_quality import classify, win_percent
from src.validators.moves_contract import validate_moves

MOVES_IN = Path("tests/fixtures/prototype_moves.json")
ANALYSIS_OUT = Path("output/content/2026-08-19-duolingo-001/analysis.json")

ENGINE_PATH = os.environ.get("STOCKFISH_PATH", "stockfish")
DEPTH = 18
MATE_SCORE = 10000


def _cp(pov_score):
    """Centipawns from the given point of view, with mate mapped to a large finite value."""
    return pov_score.score(mate_score=MATE_SCORE)


def analyse(doc, engine, depth=DEPTH):
    board = chess.Board(None)
    board.set_board_fen(doc["start_position"]["piece_placement"]["value"])
    board.turn = chess.WHITE if doc["start_position"]["side_to_move"]["value"] == "w" else chess.BLACK

    results = []
    for m in doc["moves"]:
        mover = board.turn
        played = chess.Move.from_uci(m["uci"])

        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = info["pv"][0]
        best_cp = _cp(info["score"].pov(mover))
        best_san = board.san(best_move)

        board.push(played)
        after = engine.analyse(board, chess.engine.Limit(depth=depth))
        after_cp = _cp(after["score"].pov(mover))

        drop = max(0.0, win_percent(best_cp) - win_percent(after_cp))
        played_best = played == best_move

        results.append(
            {
                "ply": m["ply"],
                "san": m["san"],
                "uci": m["uci"],
                "side": m["side"],
                "eval_before_cp": best_cp,
                "eval_after_cp": after_cp,
                "win_percent_before": round(win_percent(best_cp), 2),
                "win_percent_after": round(win_percent(after_cp), 2),
                "win_percent_drop": round(drop, 2),
                "label": classify(drop, played_best=played_best),
                "best_move_uci": best_move.uci(),
                "best_move_san": best_san,
                "played_best": played_best,
            }
        )

    return results


def main():
    doc = json.loads(MOVES_IN.read_text())

    # Only analyse what the contract lets through.
    doc = dict(doc)
    doc["moves"] = [m for m in doc["moves"] if m["verification_status"] != "unresolved"]

    errors = validate_moves(doc)
    if errors:
        raise SystemExit(f"refusing to analyse: {len(errors)} contract failures: {errors[:3]}")

    with chess.engine.SimpleEngine.popen_uci(ENGINE_PATH) as engine:
        results = analyse(doc, engine)

    owner = doc["owner_side"]
    owner_errors = [r for r in results if r["side"] == owner and r["label"] in ("blunder", "mistake", "inaccuracy")]
    worst = max(owner_errors, key=lambda r: r["win_percent_drop"], default=None)

    out = {
        "schema_version": "1.0",
        "content_id": doc["content_id"],
        "engine": {"name": "Stockfish", "depth": DEPTH},
        "owner_side": owner,
        "plies_analysed": len(results),
        "moves": results,
        "owner_worst_moment": worst,
    }

    ANALYSIS_OUT.parent.mkdir(parents=True, exist_ok=True)
    ANALYSIS_OUT.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    out = main()
    print(f"analysed {out['plies_analysed']} plies -> {ANALYSIS_OUT}\n")
    print(f"{'ply':>3} {'side':<5} {'san':<8} {'label':<11} {'drop%':>6}  best")
    for r in out["moves"]:
        mark = "  <-- owner" if r["side"] == out["owner_side"] and r["label"] in ("blunder", "mistake") else ""
        print(f"{r['ply']:>3} {r['side']:<5} {r['san']:<8} {r['label']:<11} {r['win_percent_drop']:>6.2f}  {r['best_move_san']}{mark}")
    w = out["owner_worst_moment"]
    print()
    if w:
        print(f"owner's worst moment: ply {w['ply']} {w['san']} ({w['label']}, -{w['win_percent_drop']}% win)")
        print(f"  should have played: {w['best_move_san']}")
    else:
        print("no owner mistake found in the analysed range")
