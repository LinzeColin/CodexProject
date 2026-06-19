from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

from .australia_markets import generate_australia_report
from .boards import BOARD_CONFIGS, BoardConfig, board_by_id
from .futures import generate_futures_report
from .group_betting import generate_group_report
from .pipeline import write_outputs
from .team_futures_multi import generate_team_multi_report


@dataclass(frozen=True)
class BoardRunContext:
    output_dir: Path
    previous_baseline_path: Optional[Path] = None
    public_source_audit_path: Optional[Path] = None
    event_audit_path: Optional[Path] = None


@dataclass(frozen=True)
class BoardRunner:
    board_id: str
    step_name: str
    response_prefix: str
    run: Callable[[BoardConfig, BoardRunContext], Dict]


def run_matches(board: BoardConfig, context: BoardRunContext) -> Dict:
    return write_outputs(
        context.output_dir / board.raw_snapshot,
        context.output_dir,
        version=board.version,
        previous_baseline_path=context.previous_baseline_path,
        public_source_audit_path=context.public_source_audit_path,
        event_audit_path=context.event_audit_path,
    )


def run_futures(board: BoardConfig, context: BoardRunContext) -> Dict:
    return generate_futures_report(context.output_dir / board.raw_snapshot, context.output_dir, version=board.version)


def run_group_betting(board: BoardConfig, context: BoardRunContext) -> Dict:
    return generate_group_report(context.output_dir / board.raw_snapshot, context.output_dir, version=board.version)


def run_australia_markets(board: BoardConfig, context: BoardRunContext) -> Dict:
    return generate_australia_report(context.output_dir / board.raw_snapshot, context.output_dir, version=board.version)


def run_team_futures_multi(board: BoardConfig, context: BoardRunContext) -> Dict:
    return generate_team_multi_report(context.output_dir / board.raw_snapshot, context.output_dir, version=board.version)


BOARD_RUNNERS = {
    "world_cup_matches": BoardRunner("world_cup_matches", "matches_board", "matches", run_matches),
    "world_cup_futures": BoardRunner("world_cup_futures", "futures_board", "futures", run_futures),
    "world_cup_group_betting": BoardRunner("world_cup_group_betting", "group_betting_board", "group_betting", run_group_betting),
    "world_cup_australia_markets": BoardRunner("world_cup_australia_markets", "australia_markets_board", "australia_markets", run_australia_markets),
    "world_cup_team_futures_multi": BoardRunner("world_cup_team_futures_multi", "team_futures_multi_board", "team_futures_multi", run_team_futures_multi),
}


def daily_board_registry(boards: Iterable[BoardConfig] = BOARD_CONFIGS) -> list[tuple[BoardConfig, BoardRunner]]:
    registry = []
    for board in sorted(boards, key=lambda item: item.priority):
        runner = BOARD_RUNNERS.get(board.board_id)
        if runner:
            registry.append((board, runner))
    return registry


def run_daily_boards(context: BoardRunContext, boards: Iterable[BoardConfig] = BOARD_CONFIGS) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for board, runner in daily_board_registry(boards):
        results[board.board_id] = runner.run(board, context)
    return results


def missing_runner_board_ids(boards: Iterable[BoardConfig] = BOARD_CONFIGS) -> list[str]:
    return [
        board.board_id
        for board in boards
        if board.required_for_full_automation and board.board_id not in BOARD_RUNNERS
    ]


def board_result(results: Dict[str, Dict], board_id: str) -> Dict:
    return results[board_id]


def gate_for(results: Dict[str, Dict], board_id: str) -> Dict:
    return board_result(results, board_id).get("automation_gate", {})


def recommendation_count(results: Dict[str, Dict], board_id: str) -> int:
    return len(board_result(results, board_id).get("recommendations", []))


def pre_pdf_gate_map(results: Dict[str, Dict]) -> Dict[str, Dict]:
    return {
        "matches": gate_for(results, "world_cup_matches"),
        "futures": gate_for(results, "world_cup_futures"),
        "group_betting": gate_for(results, "world_cup_group_betting"),
        "australia_markets": gate_for(results, "world_cup_australia_markets"),
        "team_futures_multi": gate_for(results, "world_cup_team_futures_multi"),
    }


def response_metrics(results: Dict[str, Dict]) -> Dict:
    matches = board_result(results, "world_cup_matches")
    matches_gate = matches.get("automation_gate", {})
    response = {
        "automation_ready": matches_gate.get("automation_ready"),
        "recommendations": recommendation_count(results, "world_cup_matches"),
        "recommended_new_exposure_aud": matches.get("recommended_new_exposure_aud", 0),
        "public_sources_ready": matches_gate.get("public_sources", {}).get("ready"),
        "event_monitor_ready": matches_gate.get("event_monitor", {}).get("ready"),
    }
    for board, runner in daily_board_registry():
        if board.board_id == "world_cup_matches":
            continue
        result = board_result(results, board.board_id)
        gate = result.get("automation_gate", {})
        response[f"{runner.response_prefix}_automation_ready"] = gate.get("automation_ready")
        response[f"{runner.response_prefix}_recommendations"] = len(result.get("recommendations", []))
        if "manual_report_ready" in gate:
            response[f"{runner.response_prefix}_manual_report_ready"] = gate.get("manual_report_ready")
    response["board_results"] = {
        board_id: {
            "automation_ready": result.get("automation_gate", {}).get("automation_ready"),
            "manual_report_ready": result.get("automation_gate", {}).get("manual_report_ready"),
            "recommendation_count": len(result.get("recommendations", [])),
            "artifact_version": result.get("version"),
        }
        for board_id, result in results.items()
    }
    return response


def board_input_paths(output_dir: Path, boards: Iterable[BoardConfig] = BOARD_CONFIGS) -> Dict[str, str]:
    inputs = {}
    for board in boards:
        if board.raw_snapshot:
            inputs[f"{board.refresh_board_id or board.board_id}_raw"] = str(output_dir / board.raw_snapshot)
    return inputs


def current_matches_board() -> BoardConfig:
    return board_by_id("world_cup_matches")
