from __future__ import annotations

from collections import deque
from math import floor
from typing import Any

from settings import GRID_HEIGHT, GRID_WIDTH, OFFICE_MAP_LAYOUT, TILE_SIZE


class OfficeMapModel:
    FLOOR = "floor"
    WALL = "wall"
    DESK = "desk"
    KITCHEN = "kitchen"
    MEETING = "meeting"
    KANBAN = "kanban"

    WALKABLE_TILES = {FLOOR, KITCHEN, MEETING, KANBAN}

    def __init__(
        self,
        tile_size: int = TILE_SIZE,
        width: int = GRID_WIDTH,
        height: int = GRID_HEIGHT,
    ) -> None:
        self.tile_size = tile_size
        self.width = width
        self.height = height
        self.layout = OFFICE_MAP_LAYOUT
        self.grid = self._build_grid()

        targets = self.layout["targets"]
        self.zone_labels = self.layout["labels"]
        self.kanban_target = targets["kanban"]
        self.kitchen_target = targets["kitchen"]
        self.meeting_target = targets["meeting"]
        self.wander_targets = [
            targets[target] if isinstance(target, str) else target
            for target in self.layout["wander_targets"]
        ]

    def is_walkable(self, grid_x: int, grid_y: int) -> bool:
        if not (0 <= grid_x < self.width and 0 <= grid_y < self.height):
            return False
        return self.grid[grid_y][grid_x] in self.WALKABLE_TILES

    def neighbors(self, cell: tuple[int, int]) -> list[tuple[int, int]]:
        grid_x, grid_y = cell
        result = []

        for offset_x, offset_y in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            next_x = grid_x + offset_x
            next_y = grid_y + offset_y
            if self.is_walkable(next_x, next_y):
                result.append((next_x, next_y))

        return result

    def cell_cost(self, cell: tuple[int, int]) -> float:
        return 1.0

    def is_rect_walkable(self, rect: tuple[int, int, int, int]) -> bool:
        left, top, width, height = rect
        right = left + width - 1
        bottom = top + height - 1

        if left < 0 or top < 0:
            return False

        min_x = floor(left / self.tile_size)
        max_x = floor(right / self.tile_size)
        min_y = floor(top / self.tile_size)
        max_y = floor(bottom / self.tile_size)

        for grid_y in range(min_y, max_y + 1):
            for grid_x in range(min_x, max_x + 1):
                if not self.is_walkable(grid_x, grid_y):
                    return False

        return True

    def grid_to_world(self, grid_x: int, grid_y: int) -> tuple[int, int]:
        return grid_x * self.tile_size, grid_y * self.tile_size

    def grid_to_center(self, grid_x: int, grid_y: int) -> tuple[int, int]:
        return (
            grid_x * self.tile_size + self.tile_size // 2,
            grid_y * self.tile_size + self.tile_size // 2,
        )

    def world_to_grid(self, world_x: int | float, world_y: int | float) -> tuple[int, int]:
        return floor(world_x / self.tile_size), floor(world_y / self.tile_size)

    # найти ближайшую точку, куда можно встать, если дано место, куда встать нельзя
    def find_nearest_walkable(self, start: tuple[int, int]) -> tuple[int, int] | None:
        # если стартовая точка уже проходимая, то и думать не надо
        if self.is_walkable(*start):
            return start

        queue = deque([start]) # очередь для обхода в ширину
        visited = {start} # пройденные клетки

        while queue:
            grid_x, grid_y = queue.popleft() # взять следующую клетку из очереди (самую близкую к старту)

            for offset_x, offset_y in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                next_cell = (grid_x + offset_x, grid_y + offset_y)
                if next_cell in visited:
                    continue

                visited.add(next_cell)
                next_x, next_y = next_cell
                if not (0 <= next_x < self.width and 0 <= next_y < self.height): # проверить, что клетка в пределах карты
                    continue

                if self.is_walkable(next_x, next_y): # если клетка норм - берем ее
                    return next_cell

                queue.append(next_cell)

        return None

    def _build_grid(self) -> list[list[str]]:
        grid = [[self.FLOOR for _ in range(self.width)] for _ in range(self.height)]

        for section, default_tile in (
            ("zones", self.FLOOR),
            ("furniture", self.DESK),
            ("walls", self.WALL),
            ("openings", self.FLOOR),
        ):
            for rect in self.layout[section]:
                self._fill_layout_rect(grid, rect, default_tile)

        return grid

    def _fill_layout_rect(
        self,
        grid: list[list[str]],
        rect: dict[str, Any],
        default_tile: str,
    ) -> None:
        tile = rect.get("tile", default_tile)
        self._fill_rect(
            grid,
            int(rect["left"]),
            int(rect["top"]),
            int(rect["width"]),
            int(rect["height"]),
            str(tile),
        )

    def _fill_rect(
        self,
        grid: list[list[str]],
        left: int,
        top: int,
        width: int,
        height: int,
        tile: str,
    ) -> None:
        for y in range(top, top + height):
            for x in range(left, left + width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    grid[y][x] = tile
