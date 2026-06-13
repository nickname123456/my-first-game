class BaseState:
    def __init__(self, game) -> None:
        self.game = game

    def handle_event(self, event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        pass
