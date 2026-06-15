from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass
class PlayerModel:
    x: int
    y: int
    width: int
    height: int
    speed: int
    interact_requested: bool = False
    direction: str = "down"
    is_moving: bool = False
    animation_time: float = 0.0

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    def move(self, dx: int, dy: int, dt: float) -> None:
        length = hypot(dx, dy)
        if length == 0:
            return

        normalized_x = dx / length
        normalized_y = dy / length
        self.x += round(normalized_x * self.speed * dt)
        self.y += round(normalized_y * self.speed * dt)

    def request_interaction(self, requested: bool) -> None:
        self.interact_requested = requested

    def set_movement_state(self, direction: str | None, is_moving: bool, dt: float) -> None:
        if direction is not None:
            self.direction = direction

        self.is_moving = is_moving
        if is_moving:
            self.animation_time += dt
        else:
            self.animation_time = 0.0
