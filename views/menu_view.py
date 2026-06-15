from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class MenuView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(86)
        self.text_font = get_ui_font(34)

    def draw(self, surface) -> None:
        title = self.title_font.render("PM Simulator", True, COLORS["text"])
        prompt = self.text_font.render("Нажмите Enter, чтобы начать", True, COLORS["muted_text"])

        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

        surface.blit(title, title_rect)
        surface.blit(prompt, prompt_rect)
