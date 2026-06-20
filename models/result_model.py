from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from models.project_stats_model import ProjectStatsModel


HIGHSCORE_FILE = "highscore.json"
TECH_DEBT_FAILURE_LIMIT = 100
MIN_RELEASE_TASKS_DONE = 6
MIN_RELEASE_BUDGET = 10
MIN_RELEASE_MORALE = 20
MIN_RELEASE_QUALITY = 35
MIN_RELEASE_CLIENT_TRUST = 35
MAX_RELEASE_TECH_DEBT = 80
EARLY_RELEASE_MAX_BONUS_RATE = 0.5


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
    base_score: int = 0
    early_release_bonus: int = 0
    score_multiplier: float = 1.0
    early_release: bool = False


def calculate_base_score(stats: ProjectStatsModel) -> int:
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


def calculate_early_release_multiplier(
    stats: ProjectStatsModel,
    release_duration: float = 180.0,
) -> float:
    if release_duration <= 0:
        return 1.0

    time_ratio = max(0.0, min(1.0, stats.release_time_left / release_duration))
    return 1.0 + time_ratio * EARLY_RELEASE_MAX_BONUS_RATE


def calculate_final_score(
    stats: ProjectStatsModel,
    early_release: bool = False,
    release_duration: float = 180.0,
) -> int:
    base_score = calculate_base_score(stats)
    if not early_release:
        return base_score

    multiplier = calculate_early_release_multiplier(stats, release_duration)
    return max(0, int(base_score * multiplier))


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


def release_failure_reason(stats: ProjectStatsModel) -> str | None:
    if stats.tasks_done < MIN_RELEASE_TASKS_DONE:
        return f"Релиз провален: выполнено {stats.tasks_done}/{MIN_RELEASE_TASKS_DONE} задач"
    if stats.budget < MIN_RELEASE_BUDGET:
        return "Релиз провален: бюджет ниже безопасного минимума"
    if stats.morale < MIN_RELEASE_MORALE:
        return "Релиз провален: команда слишком деморализована"
    if stats.quality < MIN_RELEASE_QUALITY:
        return "Релиз провален: качество продукта слишком низкое"
    if stats.client_trust < MIN_RELEASE_CLIENT_TRUST:
        return "Релиз провален: доверие заказчика слишком низкое"
    if stats.tech_debt > MAX_RELEASE_TECH_DEBT:
        return "Релиз провален: технический долг слишком высокий"
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
    early_release: bool = False,
    release_duration: float = 180.0,
) -> GameResult:
    score_multiplier = 1.0
    if early_release and won:
        score_multiplier = calculate_early_release_multiplier(stats, release_duration)

    base_score = calculate_base_score(stats)
    score = max(0, int(base_score * score_multiplier))
    early_release_bonus = max(0, score - base_score) if early_release and won else 0

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
        base_score=base_score,
        early_release_bonus=early_release_bonus,
        score_multiplier=score_multiplier,
        early_release=early_release and won,
    )


def determine_game_result(
    stats: ProjectStatsModel,
    high_score_path: str | Path | None = HIGHSCORE_FILE,
) -> GameResult | None:
    reason = failure_reason(stats)
    if reason is not None:
        return build_game_result(stats, False, reason, high_score_path)

    if stats.release_time_left <= 0:
        release_reason = release_failure_reason(stats)
        if release_reason is not None:
            return build_game_result(stats, False, release_reason, high_score_path)

        return build_game_result(
            stats,
            True,
            "Релиз успешен: минимум задач выполнен, ключевые ресурсы сохранены",
            high_score_path,
        )

    return None
