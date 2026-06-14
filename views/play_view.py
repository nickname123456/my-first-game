from models.employee_model import EmployeeModel
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import Task
from views.employee_view import EmployeeView
from views.hud_view import HudView
from views.kanban_view import KanbanView
from views.office_map_view import OfficeMapView
from views.player_view import PlayerView


class PlayView:
    def __init__(self) -> None:
        self.office_map_view = OfficeMapView()
        self.employee_view = EmployeeView()
        self.player_view = PlayerView()
        self.hud_view = HudView()
        self.kanban_view = KanbanView()

    def draw(
        self,
        surface,
        office_map: OfficeMapModel,
        player: PlayerModel,
        employees: list[EmployeeModel],
        project_stats: ProjectStatsModel,
        task_manager: TaskManager,
        sorted_tasks: list[Task],
        kanban_open: bool,
        selected_task_id: int | None,
        selected_task_index: int,
        selected_employee_index: int,
    ) -> None:
        self.office_map_view.draw(surface, office_map)
        self.employee_view.draw(surface, employees, task_manager)
        self.player_view.draw(surface, player)
        self.hud_view.draw(surface, project_stats)
        if kanban_open:
            self.kanban_view.draw(
                surface,
                sorted_tasks,
                employees,
                selected_task_id,
                selected_task_index,
                selected_employee_index,
            )

    def hit_test_kanban(self, pos: tuple[int, int]) -> tuple[str | None, int]:
        return self.kanban_view.hit_test(pos)
