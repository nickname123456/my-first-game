from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models.project_stats_model import ProjectStatsModel


HIGHSCORE_FILE = "highscore.json"
TECH_DEBT_FAILURE_LIMIT = 100


@dataclass(frozen=True)
class GameResult:
    won: bool
    reason: str
    score: int
    best_score: int
    is_new_record: bool
    tasks_done: int
    tasks_failed: int
    budget: int
    morale: int
    quality: int
    tech_debt: int
    client_trust: int


def calculate_final_score(stats: ProjectStatsModel) -> int:
    tasks_done_in_time = stats.tasks_done
    score = 0
    score += stats.tasks_done * 100
    score += tasks_done_in_time * 50
    score += stats.quality * 5
    score += stats.morale * 3
    score += stats.budget * 2
    score += stats.client_trust * 4
    score -= stats.tech_debt * 6
    return max(0, int(score))


def failure_reason(stats: ProjectStatsModel) -> str | None:
    if stats.budget <= 0:
        return "Бюджет закончился"
    if stats.morale <= 0:
        return "Мораль команды упала до нуля"
    if stats.quality <= 0:
        return "Качество продукта упало до нуля"
    if stats.client_trust <= 0:
        return "Доверие заказчика упало до нуля"
    if stats.tech_debt >= TECH_DEBT_FAILURE_LIMIT:
        return "Технический долг стал критическим"
    return None


def load_high_score(path: str | Path = HIGHSCORE_FILE) -> int:
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return 0

    raw_score = data.get("best_score", 0) if isinstance(data, dict) else data
    try:
        return max(0, int(raw_score))
    except (TypeError, ValueError):
        return 0


def save_high_score(score: int, path: str | Path = HIGHSCORE_FILE) -> int:
    current_best = load_high_score(path)
    best_score = max(current_best, max(0, int(score)))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as file:
        json.dump({"best_score": best_score}, file, ensure_ascii=False, indent=2)
    return best_score


def build_game_result(
    stats: ProjectStatsModel,
    won: bool,
    reason: str,
    high_score_path: str | Path | None = HIGHSCORE_FILE,
) -> GameResult:
    score = calculate_final_score(stats)

    if high_score_path is None:
        best_score = score
        is_new_record = score > 0
    else:
        previous_best = load_high_score(high_score_path)
        best_score = save_high_score(score, high_score_path)
        is_new_record = score > previous_best

    return GameResult(
        won=won,
        reason=reason,
        score=score,
        best_score=best_score,
        is_new_record=is_new_record,
        tasks_done=stats.tasks_done,
        tasks_failed=stats.tasks_failed,
        budget=stats.budget,
        morale=stats.morale,
        quality=stats.quality,
        tech_debt=stats.tech_debt,
        client_trust=stats.client_trust,
    )


def determine_game_result(
    stats: ProjectStatsModel,
    high_score_path: str | Path | None = HIGHSCORE_FILE,
) -> GameResult | None:
    reason = failure_reason(stats)
    if reason is not None:
        return build_game_result(stats, False, reason, high_score_path)

    if stats.release_time_left <= 0:
        return build_game_result(
            stats,
            True,
            "Время релиза закончилось, ключевые ресурсы сохранены",
            high_score_path,
        )

    return None
