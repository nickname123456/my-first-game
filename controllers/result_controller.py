import pygame

from controllers.base_scene_controller import BaseSceneController
from models.result_model import GameResult
from views.result_view import ResultView


class ResultController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.result: GameResult | None = None
        self.view = ResultView()

    def set_result(self, result: GameResult) -> None:
        self.result = result

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game_controller.change_scene("menu")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game_controller.quit()

    def draw(self, surface) -> None:
        self.view.draw(surface, self.result)
