from entities.office_map import OfficeMap
from entities.player import Player
from settings import TILE_SIZE
from states.base_state import BaseState


class PlayState(BaseState):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.office_map = OfficeMap()
        self.player = Player(TILE_SIZE * 3, TILE_SIZE * 3)

    def update(self, dt: float) -> None:
        keys = self._get_pressed_keys()
        self.player.handle_input(keys, dt)
        self.player.update(dt)

    def draw(self, surface) -> None:
        self.office_map.draw(surface)
        self.player.draw(surface)

    def _get_pressed_keys(self):
        import pygame

        return pygame.key.get_pressed()
