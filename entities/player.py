from models.player_model import PlayerModel
from settings import PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_WIDTH


class Player(PlayerModel):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED)
