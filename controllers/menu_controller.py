import pygame

from controllers.base_scene_controller import BaseSceneController
from views.menu_view import MenuView


class MenuController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.view = MenuView()

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game_controller.change_scene("play")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game_controller.quit()

    def draw(self, surface) -> None:
        self.view.draw(surface)
