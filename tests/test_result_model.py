import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from controllers.play_controller import PlayController
from models.project_stats_model import ProjectStatsModel
from models.result_model import (
    TECH_DEBT_FAILURE_LIMIT,
    calculate_final_score,
    determine_game_result,
    load_high_score,
    save_high_score,
)


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
        budget=1,
        morale=1,
        quality=1,
        tech_debt=TECH_DEBT_FAILURE_LIMIT - 1,
        client_trust=1,
    )

    result = determine_game_result(stats, tmp_path / "highscore.json")

    assert result is not None
    assert result.won is True


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
    controller.project_stats.release_time_left = 0.01

    controller.update(0.02)

    assert controller.finished is True
    assert game_controller.result is not None
    assert game_controller.result.won is True
