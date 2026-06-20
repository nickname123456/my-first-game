import pygame

from models.result_model import GameResult
from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class ResultView:
    def __init__(self) -> None:
        self.font = get_ui_font(60)
        self.subtitle_font = get_ui_font(30)
        self.text_font = get_ui_font(26)
        self.small_font = get_ui_font(22)

    def draw(self, surface, result: GameResult | None) -> None:
        if result is None:
            self._draw_centered(surface, "Итоги релиза", self.font, SCREEN_HEIGHT // 2 - 30)
            self._draw_centered(
                surface,
                "Нажмите Enter, чтобы вернуться в меню",
                self.subtitle_font,
                SCREEN_HEIGHT // 2 + 30,
                COLORS["muted_text"],
            )
            return

        panel = pygame.Rect(120, 58, SCREEN_WIDTH - 240, SCREEN_HEIGHT - 116)
        pygame.draw.rect(surface, (35, 39, 46), panel, border_radius=8)
        pygame.draw.rect(surface, COLORS["grid"], panel, width=2, border_radius=8)

        title = "Релиз успешен" if result.won else "Проект провален"
        title_color = (123, 211, 137) if result.won else (239, 109, 109)
        self._draw_centered(surface, title, self.font, 122, title_color)
        self._draw_centered(surface, result.reason, self.subtitle_font, 178, COLORS["muted_text"])

        record_text = f"Лучший счет: {result.best_score}"
        if result.is_new_record:
            record_text += "  новый рекорд"

        lines = [
            f"Итоговый счет: {result.score}",
            record_text,
            f"Задачи: выполнено {result.tasks_done}, провалено {result.tasks_failed}",
            (
                "Ресурсы: "
                f"бюджет {result.budget}, мораль {result.morale}, "
                f"качество {result.quality}"
            ),
            f"Доверие: {result.client_trust}, технический долг: {result.tech_debt}",
        ]

        if result.early_release:
            lines.insert(1, f"Базовый счет: {result.base_score}")
            lines.insert(
                2,
                (
                    f"Бонус за досрочный релиз: +{result.early_release_bonus} "
                    f"(x{result.score_multiplier:.2f})"
                ),
            )

        y = 250
        for line in lines:
            self._draw_centered(surface, line, self.text_font, y)
            y += 46

        self._draw_centered(
            surface,
            "Нажмите Enter, чтобы вернуться в меню",
            self.small_font,
            SCREEN_HEIGHT - 112,
            COLORS["muted_text"],
        )

    def _draw_centered(
        self,
        surface,
        text: str,
        font,
        y: int,
        color=COLORS["text"],
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=(SCREEN_WIDTH // 2, y)))
