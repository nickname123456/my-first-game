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
