import pygame

from controllers.base_scene_controller import BaseSceneController
from controllers.player_controller import PlayerController
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from settings import PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_WIDTH, TILE_SIZE
from views.play_view import PlayView


class PlayController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.office_map = OfficeMapModel()
        self.player = PlayerModel(
            TILE_SIZE * 3,
            TILE_SIZE * 3,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
            PLAYER_SPEED,
        )
        self.player_controller = PlayerController(self.player)
        self.view = PlayView()

    def update(self, dt: float) -> None:
        self.player_controller.handle_input(pygame.key.get_pressed(), dt)

    def draw(self, surface) -> None:
        self.view.draw(surface, self.office_map, self.player)
