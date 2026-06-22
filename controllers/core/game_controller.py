from controllers.scenes.game_over_controller import GameOverController
from controllers.scenes.intro_controller import IntroController
from controllers.scenes.menu_controller import MenuController
from controllers.scenes.play_controller import PlayController
from controllers.scenes.result_controller import ResultController
from models.results.result_model import HIGHSCORE_FILE, GameResult, load_high_score


class GameController:
    def __init__(self, game, high_score_path: str = HIGHSCORE_FILE) -> None:
        self.game = game
        self.high_score_path = high_score_path
        self.high_score = load_high_score(self.high_score_path)
        self.scenes = {
            "menu": MenuController(self),
            "intro": IntroController(self),
            "play": PlayController(self),
            "game_over": GameOverController(self),
            "result": ResultController(self),
        }
        self.current_scene = self.scenes["menu"]

    def change_scene(self, name: str) -> None:
        if name not in self.scenes:
            raise ValueError(f"Unknown game scene: {name}")
        self.current_scene = self.scenes[name]

    def start_new_game(self) -> None:
        self.scenes["play"] = PlayController(self)
        self.change_scene("play")

    def show_intro(self) -> None:
        self.change_scene("intro")

    def show_menu(self) -> None:
        self.change_scene("menu")

    def show_result(self, result: GameResult) -> None:
        self.high_score = result.best_score
        result_controller = self.scenes["result"]
        result_controller.set_result(result)
        self.change_scene("result")

    def quit(self) -> None:
        self.game.quit()


    # Пример Принципа подстановки Барбары Лисков
    # Все сцены имеют одинаковый интерфейс и могут быть взаимозаменяемыми для контроллера
    def handle_event(self, event) -> None:
        self.current_scene.handle_event(event)

    def update(self, dt: float) -> None:
        self.current_scene.update(dt)

    def draw(self, surface) -> None:
        self.current_scene.draw(surface)
