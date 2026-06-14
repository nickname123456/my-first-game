from models.player_model import PlayerModel
import pygame


KEY_W = pygame.K_w
KEY_A = pygame.K_a
KEY_S = pygame.K_s
KEY_D = pygame.K_d
KEY_E = pygame.K_e
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT


class PlayerController:
    def __init__(self, model: PlayerModel) -> None:
        self.model = model

    def handle_input(self, keys, dt: float) -> None:
        dx = 0
        dy = 0

        if self._pressed(keys, KEY_W) or self._pressed(keys, KEY_UP):
            dy -= 1
        if self._pressed(keys, KEY_S) or self._pressed(keys, KEY_DOWN):
            dy += 1
        if self._pressed(keys, KEY_A) or self._pressed(keys, KEY_LEFT):
            dx -= 1
        if self._pressed(keys, KEY_D) or self._pressed(keys, KEY_RIGHT):
            dx += 1

        self.model.move(dx, dy, dt)
        self.model.request_interaction(self._pressed(keys, KEY_E))

    def _pressed(self, keys, key: int) -> bool:
        try:
            return bool(keys[key])
        except (KeyError, IndexError):
            return False
