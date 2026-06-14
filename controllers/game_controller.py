from controllers.game_over_controller import GameOverController
from controllers.menu_controller import MenuController
from controllers.play_controller import PlayController
from controllers.result_controller import ResultController


class GameController:
    def __init__(self, game) -> None:
        self.game = game
        self.scenes = {
            "menu": MenuController(self),
            "play": PlayController(self),
            "game_over": GameOverController(self),
            "result": ResultController(self),
        }
        self.current_scene = self.scenes["menu"]

    def change_scene(self, name: str) -> None:
        if name not in self.scenes:
            raise ValueError(f"Unknown game scene: {name}")
        self.current_scene = self.scenes[name]

    def quit(self) -> None:
        self.game.quit()

    def handle_event(self, event) -> None:
        self.current_scene.handle_event(event)

    def update(self, dt: float) -> None:
        self.current_scene.update(dt)

    def draw(self, surface) -> None:
        self.current_scene.draw(surface)
