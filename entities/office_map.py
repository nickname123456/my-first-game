from settings import COLORS, GRID_HEIGHT, GRID_WIDTH, TILE_SIZE


class OfficeMap:
    FLOOR = "floor"
    WALL = "wall"
    DESK = "desk"
    KITCHEN = "kitchen"
    MEETING = "meeting"
    KANBAN = "kanban"

    WALKABLE_TILES = {FLOOR, KITCHEN, MEETING, KANBAN}

    def __init__(self, tile_size: int = TILE_SIZE) -> None:
        self.tile_size = tile_size
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.grid = self._build_grid()
        self.zone_labels = [
            ("Work Zone", (15, 4)),
            ("Kitchen", (4, 14)),
            ("Meeting", (25, 13)),
            ("Kanban", (4, 3)),
        ]

    def is_walkable(self, grid_x: int, grid_y: int) -> bool:
        if not (0 <= grid_x < self.width and 0 <= grid_y < self.height):
            return False
        return self.grid[grid_y][grid_x] in self.WALKABLE_TILES

    def grid_to_world(self, grid_x: int, grid_y: int) -> tuple[int, int]:
        return grid_x * self.tile_size, grid_y * self.tile_size

    def draw(self, surface) -> None:
        import pygame

        font = pygame.font.Font(None, 24)

        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * self.tile_size,
                    y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, COLORS[tile], rect)
                pygame.draw.rect(surface, COLORS["grid"], rect, 1)

        for label, cell in self.zone_labels:
            text = font.render(label, True, COLORS["text"])
            surface.blit(text, self.grid_to_world(*cell))

    def _build_grid(self) -> list[list[str]]:
        grid = [[self.FLOOR for _ in range(self.width)] for _ in range(self.height)]

        for x in range(self.width):
            grid[0][x] = self.WALL
            grid[self.height - 1][x] = self.WALL
        for y in range(self.height):
            grid[y][0] = self.WALL
            grid[y][self.width - 1] = self.WALL

        self._fill_rect(grid, 2, 12, 8, 5, self.KITCHEN)
        self._fill_rect(grid, 24, 11, 6, 5, self.MEETING)
        self._fill_rect(grid, 2, 2, 6, 3, self.KANBAN)

        self._fill_rect(grid, 11, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 15, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 19, 3, 2, 3, self.DESK)
        self._fill_rect(grid, 11, 8, 2, 3, self.DESK)
        self._fill_rect(grid, 15, 8, 2, 3, self.DESK)
        self._fill_rect(grid, 19, 8, 2, 3, self.DESK)

        for x in range(9, 23):
            grid[1][x] = self.WALL
        for y in range(10, 17):
            grid[y][22] = self.WALL
        for x in range(2, 10):
            grid[11][x] = self.WALL
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
