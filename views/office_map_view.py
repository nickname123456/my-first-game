import pygame

from models.office_map_model import OfficeMapModel
from settings import COLORS


class OfficeMapView:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 24)

    def draw(self, surface, model: OfficeMapModel) -> None:
        for y, row in enumerate(model.grid):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    x * model.tile_size,
                    y * model.tile_size,
                    model.tile_size,
                    model.tile_size,
                )
                pygame.draw.rect(surface, COLORS[tile], rect)
                pygame.draw.rect(surface, COLORS["grid"], rect, 1)

        for label, cell in model.zone_labels:
            text = self.font.render(label, True, COLORS["text"])
            surface.blit(text, model.grid_to_world(*cell))
