import pygame

from models.world.office_map_model import OfficeMapModel
from settings import COLORS
from views.shared.font_utils import get_ui_font


class OfficeMapView:
    FLOOR_TILES = {
        OfficeMapModel.FLOOR,
        OfficeMapModel.KITCHEN,
        OfficeMapModel.MEETING,
        OfficeMapModel.KANBAN,
        OfficeMapModel.WORKPLACE,
    }

    def __init__(self) -> None:
        self.font = get_ui_font(24)

    def draw(self, surface, model: OfficeMapModel) -> None:
        for y, row in enumerate(model.grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * model.tile_size,
                    y * model.tile_size,
                    model.tile_size,
                    model.tile_size,
                )
                if tile in self.FLOOR_TILES:
                    self._draw_floor_tile(surface, rect, tile, x, y)
                else:
                    self._draw_solid_tile(surface, rect, tile)

        for label, cell in model.zone_labels:
            text = self.font.render(label, True, COLORS["text"])
            surface.blit(text, model.grid_to_world(*cell))

    def _draw_floor_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        tile: str,
        grid_x: int,
        grid_y: int,
    ) -> None:
        base_color = COLORS[tile]
        noise = self._tile_noise(grid_x, grid_y)
        color = self._shift_color(base_color, noise)

        pygame.draw.rect(surface, color, rect)

        seam_color = self._shift_color(base_color, -18)
        highlight_color = self._shift_color(base_color, 12)
        pygame.draw.line(surface, seam_color, rect.topleft, rect.bottomleft, 1)
        pygame.draw.line(surface, seam_color, rect.topleft, rect.topright, 1)

        if (grid_x + grid_y) % 2 == 0:
            inset_rect = rect.inflate(-12, -12)
            pygame.draw.rect(surface, highlight_color, inset_rect, 1)

        if tile == OfficeMapModel.FLOOR and (grid_x * 3 + grid_y * 5) % 11 == 0:
            accent_rect = pygame.Rect(rect.left + 8, rect.top + 8, 4, 4)
            pygame.draw.rect(surface, self._shift_color(base_color, 22), accent_rect)

        if tile == OfficeMapModel.WORKPLACE:
            marker_rect = rect.inflate(-18, -18)
            pygame.draw.rect(surface, self._shift_color(base_color, 35), marker_rect, 2)
            pygame.draw.line(
                surface,
                self._shift_color(base_color, 45),
                marker_rect.midleft,
                marker_rect.midright,
                2,
            )

    def _draw_solid_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        tile: str,
    ) -> None:
        pygame.draw.rect(surface, COLORS[tile], rect)
        pygame.draw.rect(surface, COLORS["grid"], rect, 1)

        if tile == OfficeMapModel.WALL:
            pygame.draw.line(surface, (42, 46, 54), rect.topleft, rect.topright, 2)
        elif tile == OfficeMapModel.DESK:
            pygame.draw.rect(surface, (154, 112, 72), rect.inflate(-8, -8), 2)

    def _tile_noise(self, grid_x: int, grid_y: int) -> int:
        return ((grid_x * 17 + grid_y * 31 + grid_x * grid_y * 7) % 13) - 6 # псевдослучайный шум для разнообразия пола

    def _shift_color(self, color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
        return tuple(max(0, min(255, channel + amount)) for channel in color) 
