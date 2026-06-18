import pygame

from models.crisis_model import CrisisManager, describe_effect
from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class CrisisDialogView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(28)
        self.font = get_ui_font(20)
        self.small_font = get_ui_font(18)
        self.option_rects: list[pygame.Rect] = []
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    def draw(
        self,
        surface,
        crisis_manager: CrisisManager,
        crisis_id: int,
        selected_option_index: int,
    ) -> None:
        crisis = crisis_manager.get_crisis(crisis_id)
        if crisis is None:
            return

        definition = crisis_manager.get_definition(crisis)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(210, 78, SCREEN_WIDTH - 420, SCREEN_HEIGHT - 156)
        pygame.draw.rect(surface, (42, 47, 55), panel, border_radius=6)
        pygame.draw.rect(surface, COLORS["grid"], panel, 2, border_radius=6)

        self.close_rect = pygame.Rect(panel.right - 42, panel.top + 12, 28, 28)
        pygame.draw.rect(surface, COLORS["grid"], self.close_rect, 1, border_radius=4)
        self._draw_text(surface, "X", self.font, self.close_rect.x + 8, self.close_rect.y + 3)

        self._draw_text(surface, definition.title, self.title_font, panel.left + 24, panel.top + 18)
        timer_color = (235, 154, 82) if crisis.time_left <= 10 else COLORS["text"]
        self._draw_text(
            surface,
            f"{crisis.employee_name} | осталось {max(0, int(crisis.time_left))}с",
            self.font,
            panel.left + 24,
            panel.top + 54,
            timer_color,
        )
        self._draw_text(surface, definition.description, self.small_font, panel.left + 24, panel.top + 86)

        self.option_rects = []
        start_y = panel.top + 130
        for index, option in enumerate(definition.options):
            rect = pygame.Rect(panel.left + 24, start_y + index * 86, panel.width - 48, 72)
            self.option_rects.append(rect)

            fill = (54, 62, 73)
            border_color = COLORS["grid"]
            border_width = 1
            if index == selected_option_index:
                fill = (65, 82, 96)
                border_color = COLORS["accent"]
                border_width = 2

            pygame.draw.rect(surface, fill, rect, border_radius=4)
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=4)

            self._draw_text(
                surface,
                f"{index + 1}. {option.text}",
                self.font,
                rect.x + 12,
                rect.y + 8,
            )
            self._draw_text(
                surface,
                describe_effect(option.effect),
                self.small_font,
                rect.x + 12,
                rect.y + 39,
                COLORS["muted_text"],
            )

        self._draw_text(
            surface,
            "1-4 / Enter - выбрать, Esc - закрыть",
            self.small_font,
            panel.left + 24,
            panel.bottom - 34,
            COLORS["muted_text"],
        )

    def hit_test(self, pos: tuple[int, int]) -> tuple[str | None, int]:
        if self.close_rect.collidepoint(pos):
            return "close", -1
        for index, rect in enumerate(self.option_rects):
            if rect.collidepoint(pos):
                return "option", index
        return None, -1

    def _draw_text(
        self,
        surface,
        value: str,
        font: pygame.font.Font,
        x: int,
        y: int,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        text = font.render(value, True, color or COLORS["text"])
        surface.blit(text, (x, y))
