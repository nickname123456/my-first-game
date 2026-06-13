import pygame

from settings import COLORS, FPS, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from states.game_over_state import GameOverState
from states.menu_state import MenuState
from states.play_state import PlayState
from states.result_state import ResultState


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.states = {
            "menu": MenuState(self),
            "play": PlayState(self),
            "game_over": GameOverState(self),
            "result": ResultState(self),
        }
        self.current_state = self.states["menu"]

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self.current_state.update(dt)
            self._draw()

        pygame.quit()

    def change_state(self, name: str) -> None:
        if name not in self.states:
            raise ValueError(f"Unknown game state: {name}")
        self.current_state = self.states[name]

    def quit(self) -> None:
        self.running = False

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.quit()
            else:
                self.current_state.handle_event(event)

    def _draw(self) -> None:
        self.screen.fill(COLORS["background"])
        self.current_state.draw(self.screen)
        pygame.display.flip()
