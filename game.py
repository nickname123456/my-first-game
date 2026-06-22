import pygame

from settings import COLORS, FPS, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from controllers.core.game_controller import GameController


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.controller = GameController(self)


    # Пример KISS
    # Каждый кадр состоит из трёх очевидных этапов: 
    # обработать события, обновить состояние и нарисовать результат. 
    # Цикл не содержит игровую бизнес-логику и только координирует системы
    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self.controller.update(dt)
            self._draw()

        pygame.quit()

    def change_state(self, name: str) -> None:
        self.controller.change_scene(name)

    def quit(self) -> None:
        self.running = False

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            else:
                self.controller.handle_event(event)

    def _draw(self) -> None:
        self.screen.fill(COLORS["background"])
        self.controller.draw(self.screen)
        pygame.display.flip()
