import pygame

from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.shared.font_utils import get_ui_font


PAUSE_ACTIONS = (
    ("resume", "Продолжить"),
    ("main_menu", "В главное меню"),
)


class PauseView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(42)
        self.button_font = get_ui_font(26)
        self.hint_font = get_ui_font(18)
        self.button_rects: list[pygame.Rect] = []

    def draw(self, surface, selected_action_index: int) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, 440, 310)
        panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(surface, (42, 47, 55), panel, border_radius=8)
        pygame.draw.rect(surface, COLORS["grid"], panel, 2, border_radius=8)

        title = self.title_font.render("Пауза", True, COLORS["text"])
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 56)))

        self.button_rects = []
        for index, (_, label) in enumerate(PAUSE_ACTIONS):
            rect = pygame.Rect(panel.left + 60, panel.top + 104 + index * 72, 320, 54)
            self.button_rects.append(rect)
            selected = index == selected_action_index
            fill = (65, 82, 96) if selected else (54, 62, 73)
            border_color = COLORS["accent"] if selected else COLORS["grid"]
            border_width = 2 if selected else 1
            pygame.draw.rect(surface, fill, rect, border_radius=5)
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=5)

            text = self.button_font.render(label, True, COLORS["text"])
            surface.blit(text, text.get_rect(center=rect.center))

        hint = self.hint_font.render(
            "Стрелки / Enter — выбрать, Esc — продолжить",
            True,
            COLORS["muted_text"],
        )
        surface.blit(hint, hint.get_rect(center=(panel.centerx, panel.bottom - 28)))

    def hit_test(self, pos: tuple[int, int]) -> str | None:
        for index, rect in enumerate(self.button_rects):
            if rect.collidepoint(pos):
                return PAUSE_ACTIONS[index][0]
        return None
