from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from views.office_map_view import OfficeMapView
from views.player_view import PlayerView


class PlayView:
    def __init__(self) -> None:
        self.office_map_view = OfficeMapView()
        self.player_view = PlayerView()

    def draw(
        self,
        surface,
        office_map: OfficeMapModel,
        player: PlayerModel,
    ) -> None:
        self.office_map_view.draw(surface, office_map)
        self.player_view.draw(surface, player)
