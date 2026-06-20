import pygame

from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.shared.font_utils import get_ui_font


class IntroView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(54)
        self.subtitle_font = get_ui_font(28)
        self.text_font = get_ui_font(23)
        self.small_font = get_ui_font(19)

    def draw(self, surface) -> None:
        panel = pygame.Rect(130, 76, SCREEN_WIDTH - 260, SCREEN_HEIGHT - 152)
        pygame.draw.rect(surface, (35, 39, 46), panel, border_radius=8)
        pygame.draw.rect(surface, COLORS["grid"], panel, 2, border_radius=8)

        content_x = panel.left + 56
        content_width = panel.width - 112

        self._draw_centered(surface, "Перед релизом", self.title_font, panel.top + 58)
        self._draw_centered(
            surface,
            "Вы - PM небольшой IT-команды. Заказчик уверен, что все почти готово. Конечно.",
            self.small_font,
            panel.top + 110,
            COLORS["muted_text"],
        )

        story_text = (
            "До релиза осталось несколько минут. Открывайте канбан, назначайте задачи "
            "подходящим специалистам и тушите кризисы. Цель простая: выпустить продукт "
            "и не уничтожить бюджет, качество, мораль и доверие."
        )
        story_bottom = self._draw_wrapped_text(
            surface,
            story_text,
            self.text_font,
            content_x,
            panel.top + 160,
            content_width,
            32,
        )

        control_title = self.subtitle_font.render("Управление", True, COLORS["text"])
        surface.blit(control_title, (content_x, story_bottom + 34))

        controls = [
            "WASD / стрелки - движение по офису",
            "E - открыть канбан или помочь сотруднику",
            "Enter - подтвердить выбор",
            "R - досрочный релиз, если все задачи закрыты",
            "Esc - назад или выход",
        ]
        self._draw_lines(surface, controls, content_x, story_bottom + 80, 29, COLORS["muted_text"])

        self._draw_centered(
            surface,
            "Enter - начать релиз    Esc - вернуться в меню",
            self.text_font,
            panel.bottom - 38,
            COLORS["accent"],
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

    def _draw_lines(
        self,
        surface,
        lines: list[str],
        x: int,
        y: int,
        line_height: int,
        color=COLORS["text"],
    ) -> None:
        for index, line in enumerate(lines):
            rendered = self.text_font.render(line, True, color)
            surface.blit(rendered, (x, y + index * line_height))

    def _draw_wrapped_text(
        self,
        surface,
        text: str,
        font,
        x: int,
        y: int,
        max_width: int,
        line_height: int,
        color=COLORS["text"],
    ) -> int:
        line = ""
        current_y = y

        for word in text.split():
            candidate = word if not line else f"{line} {word}"
            if font.size(candidate)[0] <= max_width:
                line = candidate
                continue

            if line:
                rendered = font.render(line, True, color)
                surface.blit(rendered, (x, current_y))
                current_y += line_height
            line = word

        if line:
            rendered = font.render(line, True, color)
            surface.blit(rendered, (x, current_y))
            current_y += line_height

        return current_y
