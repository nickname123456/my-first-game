from models.employee_model import EmployeeModel
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from models.project_stats_model import ProjectStatsModel
from views.employee_view import EmployeeView
from views.hud_view import HudView
from views.office_map_view import OfficeMapView
from views.player_view import PlayerView


class PlayView:
    def __init__(self) -> None:
        self.office_map_view = OfficeMapView()
        self.employee_view = EmployeeView()
        self.player_view = PlayerView()
        self.hud_view = HudView()

    def draw(
        self,
        surface,
        office_map: OfficeMapModel,
        player: PlayerModel,
        employees: list[EmployeeModel],
        project_stats: ProjectStatsModel,
    ) -> None:
        self.office_map_view.draw(surface, office_map)
        self.employee_view.draw(surface, employees)
        self.player_view.draw(surface, player)
        self.hud_view.draw(surface, project_stats)
