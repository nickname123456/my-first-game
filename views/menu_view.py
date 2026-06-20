from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.font_utils import get_ui_font


class MenuView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(86)
        self.text_font = get_ui_font(34)
        self.record_font = get_ui_font(28)

    def draw(self, surface, high_score: int) -> None:
        title = self.title_font.render("PM Simulator", True, COLORS["text"])
        prompt = self.text_font.render("Нажмите Enter, чтобы начать", True, COLORS["muted_text"])
        record = self.record_font.render(f"Лучший счет: {high_score}", True, COLORS["muted_text"])

        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        record_rect = record.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))

        surface.blit(title, title_rect)
        surface.blit(prompt, prompt_rect)
        surface.blit(record, record_rect)
