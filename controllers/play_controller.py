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
        return [
            EmployeeModel(
                "Anton",
                "backend",
                TILE_SIZE * 10 + 7,
                TILE_SIZE * 6 + 5,
                employee_width,
                employee_height,
                (80, 164, 222),
            ),
            EmployeeModel(
                "Mira",
                "frontend",
                TILE_SIZE * 14 + 7,
                TILE_SIZE * 6 + 5,
                employee_width,
                employee_height,
                (222, 134, 80),
            ),
            EmployeeModel(
                "Lena",
                "QA",
                TILE_SIZE * 18 + 7,
                TILE_SIZE * 6 + 5,
                employee_width,
                employee_height,
                (122, 190, 95),
            ),
            EmployeeModel(
                "Oleg",
                "DevOps",
                TILE_SIZE * 10 + 7,
                TILE_SIZE * 9 + 5,
                employee_width,
                employee_height,
                (185, 128, 220),
            ),
            EmployeeModel(
                "Ilya",
                "AI",
                TILE_SIZE * 18 + 7,
                TILE_SIZE * 11 + 5,
                employee_width,
                employee_height,
                (220, 190, 84),
            ),
        ]
