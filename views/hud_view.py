import pygame

from models.project_stats_model import ProjectStatsModel
from settings import COLORS, SCREEN_WIDTH
from views.font_utils import get_ui_font


class HudView:
    def __init__(self) -> None:
        self.font = get_ui_font(22)

    def draw(self, surface, stats: ProjectStatsModel) -> None:
        panel = pygame.Rect(0, 0, SCREEN_WIDTH, 36)
        pygame.draw.rect(surface, (35, 39, 46), panel)
        pygame.draw.line(surface, COLORS["grid"], panel.bottomleft, panel.bottomright, 2)

        values = [
            f"Релиз: {int(stats.release_time_left)}с",
            f"Бюджет: {stats.budget}",
            f"Мораль: {stats.morale}",
            f"Качество: {stats.quality}",
            f"Долг: {stats.tech_debt}",
            f"Доверие: {stats.client_trust}",
            f"Кризисы: {stats.active_crises}",
        ]
        text = self.font.render("   ".join(values), True, COLORS["text"])
        surface.blit(text, (16, 9))
