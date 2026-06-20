import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.intro_controller import IntroController
from controllers.play_controller import PlayController
from controllers.game_controller import GameController


class DummyGame:
    def __init__(self) -> None:
        self.quit_called = False

    def quit(self) -> None:
        self.quit_called = True


def key_down(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key})


def make_controller(tmp_path) -> GameController:
    pygame.init()
    return GameController(DummyGame(), high_score_path=str(tmp_path / "highscore.json"))


def test_menu_enter_opens_intro_screen(tmp_path) -> None:
    controller = make_controller(tmp_path)

    controller.handle_event(key_down(pygame.K_RETURN))

    assert isinstance(controller.current_scene, IntroController)


def test_intro_escape_returns_to_menu(tmp_path) -> None:
    controller = make_controller(tmp_path)
    controller.show_intro()

    controller.handle_event(key_down(pygame.K_ESCAPE))

    assert controller.current_scene is controller.scenes["menu"]


def test_intro_enter_starts_new_game(tmp_path) -> None:
    controller = make_controller(tmp_path)
    controller.show_intro()

    controller.handle_event(key_down(pygame.K_RETURN))

    assert isinstance(controller.current_scene, PlayController)
