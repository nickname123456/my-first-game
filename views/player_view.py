import pygame

from models.player_model import PlayerModel
from settings import COLORS


class PlayerView:
    def draw(self, surface, model: PlayerModel) -> None:
        rect = pygame.Rect(*model.rect)
        pygame.draw.rect(surface, COLORS["player"], rect)
        pygame.draw.rect(surface, COLORS["player_outline"], rect, 2)
