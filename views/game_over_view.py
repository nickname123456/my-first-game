from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class GameOverView:
    def __init__(self) -> None:
        self.font = get_ui_font(60)
        self.text_font = get_ui_font(30)

    def draw(self, surface) -> None:
        title = self.font.render("Игра окончена", True, COLORS["text"])
        prompt = self.text_font.render("Нажмите Enter, чтобы вернуться в меню", True, COLORS["muted_text"])

        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))
        surface.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))
