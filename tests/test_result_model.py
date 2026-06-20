import pytest

from models.entities.project_stats_model import ProjectStatsModel
from models.results.result_model import (
    MAX_RELEASE_TECH_DEBT,
    MIN_RELEASE_BUDGET,
    MIN_RELEASE_CLIENT_TRUST,
    MIN_RELEASE_MORALE,
    MIN_RELEASE_QUALITY,
    MIN_RELEASE_TASKS_DONE,
    TECH_DEBT_FAILURE_LIMIT,
    calculate_base_score,
    calculate_final_score,
    determine_game_result,
    load_high_score,
    save_high_score,
)


def test_final_score_never_becomes_negative() -> None:
    stats = ProjectStatsModel(
        budget=0,
        morale=0,
        quality=0,
        tech_debt=100,
        client_trust=0,
    )

    assert calculate_final_score(stats) == 0


def test_early_release_score_uses_time_multiplier() -> None:
    stats = ProjectStatsModel(
        release_time_left=90,
        budget=100,
        morale=100,
        quality=100,
        tech_debt=0,
        client_trust=100,
        tasks_done=MIN_RELEASE_TASKS_DONE,
    )
    base_score = calculate_base_score(stats)

    assert calculate_final_score(stats, early_release=True, release_duration=180) == int(
        base_score * 1.25
    )


def test_new_high_score_is_saved_when_score_is_higher(tmp_path) -> None:
    high_score_path = tmp_path / "highscore.json"

    saved_score = save_high_score(250, high_score_path)

    assert saved_score == 250
    assert load_high_score(high_score_path) == 250


def test_old_high_score_is_not_replaced_by_lower_score(tmp_path) -> None:
    high_score_path = tmp_path / "highscore.json"
    save_high_score(250, high_score_path)

    saved_score = save_high_score(100, high_score_path)

    assert saved_score == 250
    assert load_high_score(high_score_path) == 250


def test_victory_triggers_when_release_time_is_over_and_resources_are_alive(tmp_path) -> None:
    stats = ProjectStatsModel(
        release_time_left=0,
        budget=MIN_RELEASE_BUDGET,
        morale=MIN_RELEASE_MORALE,
        quality=MIN_RELEASE_QUALITY,
        tech_debt=MAX_RELEASE_TECH_DEBT,
        client_trust=MIN_RELEASE_CLIENT_TRUST,
        tasks_done=MIN_RELEASE_TASKS_DONE,
    )

    result = determine_game_result(stats, tmp_path / "highscore.json")

    assert result is not None
    assert result.won is True


def test_release_fails_when_minimum_task_count_is_not_met(tmp_path) -> None:
    stats = ProjectStatsModel(
        release_time_left=0,
        budget=100,
        morale=100,
        quality=100,
        tech_debt=0,
        client_trust=100,
        tasks_done=MIN_RELEASE_TASKS_DONE - 1,
    )

    result = determine_game_result(stats, tmp_path / "highscore.json")

    assert result is not None
    assert result.won is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("budget", MIN_RELEASE_BUDGET - 1),
        ("morale", MIN_RELEASE_MORALE - 1),
        ("quality", MIN_RELEASE_QUALITY - 1),
        ("client_trust", MIN_RELEASE_CLIENT_TRUST - 1),
        ("tech_debt", MAX_RELEASE_TECH_DEBT + 1),
    ),
)
def test_release_fails_when_final_resource_threshold_is_missed(
    tmp_path,
    field_name: str,
    value: int,
) -> None:
    stats = ProjectStatsModel(
        release_time_left=0,
        budget=100,
        morale=100,
        quality=100,
        tech_debt=0,
        client_trust=100,
        tasks_done=MIN_RELEASE_TASKS_DONE,
    )
    setattr(stats, field_name, value)

    result = determine_game_result(stats, tmp_path / "highscore.json")

    assert result is not None
    assert result.won is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("budget", 0),
        ("morale", 0),
        ("quality", 0),
        ("client_trust", 0),
        ("tech_debt", TECH_DEBT_FAILURE_LIMIT),
    ),
)
def test_defeat_triggers_on_critical_resources(tmp_path, field_name: str, value: int) -> None:
    stats = ProjectStatsModel(release_time_left=90)
    setattr(stats, field_name, value)

    result = determine_game_result(stats, tmp_path / "highscore.json")

    assert result is not None
    assert result.won is False
