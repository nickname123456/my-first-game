import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from controllers.play_controller import PlayController
from models.project_stats_model import ProjectStatsModel
from models.result_model import (
    MAX_RELEASE_TECH_DEBT,
    MIN_RELEASE_BUDGET,
    MIN_RELEASE_CLIENT_TRUST,
    MIN_RELEASE_MORALE,
    MIN_RELEASE_QUALITY,
    MIN_RELEASE_TASKS_DONE,
    TECH_DEBT_FAILURE_LIMIT,
    build_game_result,
    calculate_base_score,
    calculate_final_score,
    determine_game_result,
    load_high_score,
    save_high_score,
)
from models.task_model import TASK_STATUS_DONE, Task


class DummyGameController:
    def __init__(self, high_score_path: str) -> None:
        self.high_score_path = high_score_path
        self.result = None

    def show_result(self, result) -> None:
        self.result = result

    def quit(self) -> None:
        pass


def test_final_score_never_becomes_negative() -> None:
    stats = ProjectStatsModel(
        budget=0,
        morale=0,
        quality=0,
        tech_debt=100,
        client_trust=0,
    )

    assert calculate_final_score(stats) == 0


def test_default_final_score_matches_base_score() -> None:
    stats = ProjectStatsModel(
        release_time_left=90,
        budget=80,
        morale=70,
        quality=75,
        tech_debt=10,
        client_trust=85,
        tasks_done=8,
    )

    assert calculate_final_score(stats) == calculate_base_score(stats)


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


def test_early_release_score_multiplier_is_capped() -> None:
    stats = ProjectStatsModel(
        release_time_left=360,
        budget=100,
        morale=100,
        quality=100,
        tech_debt=0,
        client_trust=100,
        tasks_done=MIN_RELEASE_TASKS_DONE,
    )
    base_score = calculate_base_score(stats)

    assert calculate_final_score(stats, early_release=True, release_duration=180) == int(
        base_score * 1.5
    )


def test_regular_result_does_not_receive_early_release_bonus() -> None:
    stats = ProjectStatsModel(
        release_time_left=90,
        budget=100,
        morale=100,
        quality=100,
        tech_debt=0,
        client_trust=100,
        tasks_done=MIN_RELEASE_TASKS_DONE,
    )

    result = build_game_result(stats, True, "ok", high_score_path=None)

    assert result.early_release is False
    assert result.early_release_bonus == 0
    assert result.score_multiplier == 1.0
    assert result.score == result.base_score


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


def test_broken_high_score_file_is_read_as_zero(tmp_path) -> None:
    high_score_path = tmp_path / "highscore.json"
    high_score_path.write_text("{broken json", encoding="utf-8")

    assert load_high_score(high_score_path) == 0


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
    assert "выполнено" in result.reason


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


def test_play_controller_sends_release_end_to_result_scene(tmp_path) -> None:
    pygame.init()
    game_controller = DummyGameController(str(tmp_path / "highscore.json"))
    controller = PlayController(game_controller)
    controller.task_manager.tasks = [
        Task(
            id=index + 1,
            title=f"Done {index + 1}",
            required_skill="backend",
            difficulty=1,
            deadline=10,
            business_value=1,
            estimated_time=1,
            status=TASK_STATUS_DONE,
            progress=100,
        )
        for index in range(MIN_RELEASE_TASKS_DONE)
    ]
    controller.project_stats.release_time_left = 0.01

    controller.update(0.02)

    assert controller.finished is True
    assert game_controller.result is not None
    assert game_controller.result.won is True
