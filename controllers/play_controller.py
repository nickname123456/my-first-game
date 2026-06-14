import pygame

from controllers.base_scene_controller import BaseSceneController
from controllers.player_controller import PlayerController
from models.employee_model import EmployeeModel
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from models.project_stats_model import ProjectStatsModel
from settings import PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_WIDTH, TILE_SIZE
from views.play_view import PlayView


class PlayController(BaseSceneController):
    def __init__(self, game_controller) -> None:
        self.game_controller = game_controller
        self.office_map = OfficeMapModel()
        self.player = PlayerModel(
            TILE_SIZE * 3,
            TILE_SIZE * 6,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
            PLAYER_SPEED,
        )
        self.player_controller = PlayerController(self.player, self.office_map)
        self.employees = self._create_employees()
        self.project_stats = ProjectStatsModel()
        self.view = PlayView()

    def update(self, dt: float) -> None:
        self.player_controller.handle_input(pygame.key.get_pressed(), dt)

    def draw(self, surface) -> None:
        self.view.draw(
            surface,
            self.office_map,
            self.player,
            self.employees,
            self.project_stats,
        )

    def _create_employees(self) -> list[EmployeeModel]:
        employee_width = 26
        employee_height = 30
        employee_specs = [
            ("Anton", "backend", (11, 3, 2, 3)),
            ("Mira", "frontend", (15, 3, 2, 3)),
            ("Lena", "QA", (19, 3, 2, 3)),
            ("Oleg", "DevOps", (11, 8, 2, 3)),
            ("Ilya", "AI", (15, 8, 2, 3)),
        ]

        employees = []
        for name, role, desk in employee_specs:
            x, y = self._employee_position_left_of_desk(desk, employee_height)
            employees.append(
                EmployeeModel(name, role, x, y, employee_width, employee_height)
            )

        return employees

    def _employee_position_left_of_desk(
        self,
        desk: tuple[int, int, int, int],
        employee_height: int,
    ) -> tuple[int, int]:
        desk_left, desk_top, _desk_width, desk_height = desk
        x = (desk_left - 1) * TILE_SIZE + 7
        y = desk_top * TILE_SIZE + (desk_height * TILE_SIZE - employee_height) // 2
        return x, y
