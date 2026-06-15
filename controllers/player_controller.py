from math import hypot

import pygame

from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel


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
    def __init__(self, model: PlayerModel, office_map: OfficeMapModel) -> None:
        self.model = model
        self.office_map = office_map

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

        direction = self._direction_from_input(dx, dy)
        moved = self._move_with_collisions(dx, dy, dt)
        self.model.set_movement_state(direction, moved, dt)
        self.model.request_interaction(self._pressed(keys, KEY_E))

    def _move_with_collisions(self, dx: int, dy: int, dt: float) -> bool:
        length = hypot(dx, dy)
        if length == 0:
            return False

        normalized_x = dx / length
        normalized_y = dy / length
        move_x = round(normalized_x * self.model.speed * dt)
        move_y = round(normalized_y * self.model.speed * dt)
        moved = False

        if move_x:
            next_rect = (
                self.model.x + move_x,
                self.model.y,
                self.model.width,
                self.model.height,
            )
            if self.office_map.is_rect_walkable(next_rect):
                self.model.x += move_x
                moved = True

        if move_y:
            next_rect = (
                self.model.x,
                self.model.y + move_y,
                self.model.width,
                self.model.height,
            )
            if self.office_map.is_rect_walkable(next_rect):
                self.model.y += move_y
                moved = True

        return moved

    def _direction_from_input(self, dx: int, dy: int) -> str | None:
        if dx < 0:
            return "left"
        if dx > 0:
            return "right"
        if dy < 0:
            return "up"
        if dy > 0:
            return "down"
        return None

    def _pressed(self, keys, key: int) -> bool:
        try:
            return bool(keys[key])
        except (KeyError, IndexError):
            return False
