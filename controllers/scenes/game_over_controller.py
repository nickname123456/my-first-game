import pygame

from controllers.core.base_scene_controller import BaseSceneController
from views.scenes.game_over_view import GameOverView


class GameOverController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.view = GameOverView()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game_controller.change_scene("menu")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game_controller.quit()

    def draw(self, surface) -> None:
        self.view.draw(surface)
