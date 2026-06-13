import pygame

from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from states.base_state import BaseState


class GameOverState(BaseState):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.font = pygame.font.Font(None, 60)
        self.text_font = pygame.font.Font(None, 30)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game.change_state("menu")

    def draw(self, surface) -> None:
        title = self.font.render("Game Over", True, COLORS["text"])
        prompt = self.text_font.render("Press Enter to return to menu", True, COLORS["muted_text"])
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))
        surface.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))
