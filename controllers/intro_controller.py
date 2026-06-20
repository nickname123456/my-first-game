import pygame

from controllers.base_scene_controller import BaseSceneController
from views.intro_view import IntroView


class IntroController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.view = IntroView()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game_controller.start_new_game()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game_controller.change_scene("menu")

    def draw(self, surface) -> None:
        self.view.draw(surface)
