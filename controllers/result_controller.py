import pygame

from controllers.base_scene_controller import BaseSceneController
from views.result_view import ResultView


class ResultController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.view = ResultView()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game_controller.change_scene("menu")

    def draw(self, surface) -> None:
        self.view.draw(surface)
