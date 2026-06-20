import pygame

from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class GameplayHintView:
    def __init__(self) -> None:
        self.font = get_ui_font(20)

    def draw(self, surface, hint_text: str | None) -> None:
        if not hint_text:
            return

        hint_text = self._trim_to_width(hint_text, SCREEN_WIDTH - 120)
        rendered = self.font.render(hint_text, True, COLORS["text"])
        width = min(SCREEN_WIDTH - 96, rendered.get_width() + 42)
        rect = pygame.Rect(0, 0, width, 42)
        rect.centerx = SCREEN_WIDTH // 2
        rect.bottom = SCREEN_HEIGHT - 14

        pygame.draw.rect(surface, (35, 39, 46), rect, border_radius=6)
        pygame.draw.rect(surface, COLORS["accent"], rect, 2, border_radius=6)
        surface.blit(rendered, rendered.get_rect(center=rect.center))

    def _trim_to_width(self, text: str, max_width: int) -> str:
        if self.font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        trimmed = text
        while trimmed and self.font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return trimmed + ellipsis
