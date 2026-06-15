from __future__ import annotations

from collections import deque
from math import floor

from settings import GRID_HEIGHT, GRID_WIDTH, TILE_SIZE


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
        self.grid = self._build_grid()
        self.zone_labels = [
            ("Рабочая зона", (15, 4)),
            ("Кухня", (4, 14)),
            ("Переговорка", (25, 13)),
            ("Канбан", (4, 3)),
        ]
        self.kanban_target = (5, 3)
        self.kitchen_target = (5, 14)
        self.meeting_target = (26, 13)
        self.wander_targets = [
            (5, 6),
            (9, 8),
            (14, 14),
            (24, 7),
            self.kitchen_target,
            self.meeting_target,
            self.kanban_target,
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
        # залить карту полом
        # первый цикл - сделать строку
        # второй цикл - растянуть
        grid = [[self.FLOOR for _ in range(self.width)] for _ in range(self.height)]

        # обложить карту стенами сверху, снизу
        for x in range(self.width):
            grid[0][x] = self.WALL
            grid[self.height - 1][x] = self.WALL
        # обложить карту стенами слева, справа
        for y in range(self.height):
            grid[y][0] = self.WALL
            grid[y][self.width - 1] = self.WALL

        # добавить зоны
        self._fill_rect(grid, 2, 12, 8, 5, self.KITCHEN)
        self._fill_rect(grid, 24, 11, 6, 5, self.MEETING)
        self._fill_rect(grid, 2, 2, 6, 3, self.KANBAN)

        # добавить столы
        self._fill_rect(grid, 11, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 15, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 19, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 11, 8, 2, 3, self.DESK)
        self._fill_rect(grid, 15, 8, 2, 3, self.DESK)
        self._fill_rect(grid, 19, 8, 2, 3, self.DESK)

        # добавить стены внутри офиса
        for x in range(9, 23):
            grid[1][x] = self.WALL
        for y in range(10, 17):
            grid[y][22] = self.WALL
        for x in range(2, 10):
            grid[11][x] = self.WALL
        
        # добавить проходы
        grid[11][5] = self.FLOOR
        grid[11][6] = self.FLOOR

        return grid

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
