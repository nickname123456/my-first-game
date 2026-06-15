import pygame

from controllers.base_scene_controller import BaseSceneController
from models.employee_behavior_model import EmployeeBehaviorSystem
from controllers.player_controller import PlayerController
from models.employee_model import EmployeeModel
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from settings import (
    CHARACTER_HITBOX_HEIGHT,
    CHARACTER_HITBOX_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    TILE_SIZE,
)
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
        self.employee_behavior = EmployeeBehaviorSystem()
        self.project_stats = ProjectStatsModel()
        self.task_manager = TaskManager(
            release_duration=self.project_stats.release_time_left,
        )
        self.task_manager.sync_stats(self.project_stats)
        self.kanban_open = False
        self.selected_task_id: int | None = None
        self.selected_task_index = 0
        self.selected_employee_index = 0
        self.view = PlayView()

    def handle_event(self, event) -> None:
        if self.kanban_open:
            self._handle_kanban_event(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_controller.quit()
            elif event.key == pygame.K_e and self._player_is_near_kanban():
                self._open_kanban()

    def update(self, dt: float) -> None:
        self.project_stats.release_time_left = max(
            0.0,
            self.project_stats.release_time_left - dt,
        )
        self.employee_behavior.update(dt, self.employees, self.office_map)
        self.task_manager.update(dt, self.employees, self.project_stats)

        if not self.kanban_open:
            self.player_controller.handle_input(pygame.key.get_pressed(), dt)

    def draw(self, surface) -> None:
        current_time = self.task_manager.elapsed_time(self.project_stats)
        sorted_tasks = self.task_manager.sorted_active_tasks(current_time)
        self.view.draw(
            surface,
            self.office_map,
            self.player,
            self.employees,
            self.project_stats,
            self.task_manager,
            sorted_tasks,
            self.kanban_open,
            self.selected_task_id,
            self.selected_task_index,
            self.selected_employee_index,
        )

    def _handle_kanban_event(self, event) -> None:
        sorted_tasks = self._sorted_tasks()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_e):
                self.kanban_open = False
            elif event.key == pygame.K_UP:
                self.selected_task_index = self._move_selection(
                    self.selected_task_index,
                    -1,
                    len(sorted_tasks),
                )
                self._select_task_by_index(sorted_tasks)
            elif event.key == pygame.K_DOWN:
                self.selected_task_index = self._move_selection(
                    self.selected_task_index,
                    1,
                    len(sorted_tasks),
                )
                self._select_task_by_index(sorted_tasks)
            elif event.key == pygame.K_LEFT:
                self.selected_employee_index = self._move_selection(
                    self.selected_employee_index,
                    -1,
                    len(self.employees),
                )
            elif event.key == pygame.K_RIGHT:
                self.selected_employee_index = self._move_selection(
                    self.selected_employee_index,
                    1,
                    len(self.employees),
                )
            elif event.key == pygame.K_RETURN:
                self._assign_selected_task()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit_type, hit_index = self.view.hit_test_kanban(event.pos)
            if hit_type == "task":
                self.selected_task_index = hit_index
                self._select_task_by_index(sorted_tasks)
            elif hit_type == "employee":
                self.selected_employee_index = hit_index
                self._assign_selected_task()
            elif hit_type == "assign":
                self._assign_selected_task()
            elif hit_type == "close":
                self.kanban_open = False

    def _create_employees(self) -> list[EmployeeModel]:
        employee_width = CHARACTER_HITBOX_WIDTH
        employee_height = CHARACTER_HITBOX_HEIGHT
        employee_specs = [
            ("Яков", "backend", (11, 3, 2, 3)),
            ("Кира", "frontend", (15, 3, 2, 3)),
            ("Шура", "QA", (19, 3, 2, 3)),
            ("Тимур", "DevOps", (11, 8, 2, 3)),
            ("Алик", "AI", (15, 8, 2, 3)),
        ]

        employees = []
        for name, role, desk in employee_specs:
            work_cell = self._employee_cell_left_of_desk(desk)
            x, y = self._employee_position_for_cell(work_cell, employee_width, employee_height)
            employees.append(
                EmployeeModel(
                    name,
                    role,
                    x,
                    y,
                    employee_width,
                    employee_height,
                    work_cell=work_cell,
                )
            )

        return employees

    def _employee_cell_left_of_desk(
        self,
        desk: tuple[int, int, int, int],
    ) -> tuple[int, int]:
        desk_left, desk_top, _desk_width, desk_height = desk
        return desk_left - 1, desk_top + desk_height // 2

    def _employee_position_for_cell(
        self,
        cell: tuple[int, int],
        employee_width: int,
        employee_height: int,
    ) -> tuple[int, int]:
        center_x, center_y = self.office_map.grid_to_center(*cell)
        x = center_x - employee_width // 2
        y = center_y - employee_height // 2
        return x, y

    def _open_kanban(self) -> None:
        self.kanban_open = True
        self._clamp_kanban_selection()

    def _assign_selected_task(self) -> None:
        sorted_tasks = self._sorted_tasks()
        if not sorted_tasks or not self.employees or self.selected_task_id is None:
            return

        self._clamp_kanban_selection()
        task = self.task_manager.get_task(self.selected_task_id)
        if task is None:
            self.selected_task_id = None
            self._clamp_kanban_selection()
            return

        employee = self.employees[self.selected_employee_index]
        assigned = self.task_manager.assign_task(task.id, employee)
        if assigned:
            self.selected_task_id = None
        self._clamp_kanban_selection()

    def _sorted_tasks(self):
        current_time = self.task_manager.elapsed_time(self.project_stats)
        return self.task_manager.sorted_active_tasks(current_time)

    def _select_task_by_index(self, sorted_tasks) -> None:
        if not sorted_tasks:
            self.selected_task_id = None
            return
        self.selected_task_index = min(
            max(self.selected_task_index, 0),
            len(sorted_tasks) - 1,
        )
        self.selected_task_id = sorted_tasks[self.selected_task_index].id

    def _move_selection(self, current: int, delta: int, count: int) -> int:
        if count <= 0:
            return 0
        return (current + delta) % count

    def _clamp_kanban_selection(self) -> None:
        sorted_tasks = self._sorted_tasks()
        task_count = len(sorted_tasks)
        employee_count = len(self.employees)

        if self.selected_task_id is not None:
            matching_index = None

            for index, task in enumerate(sorted_tasks):
                if task.id == self.selected_task_id:
                    matching_index = index
                    break

            if matching_index is None:
                self.selected_task_id = None
            else:
                self.selected_task_index = matching_index

        if self.selected_task_index < 0:
            self.selected_task_index = 0

        if self.selected_task_index >= task_count:
            if task_count > 0:
                self.selected_task_index = task_count - 1
            else:
                self.selected_task_index = 0

        if self.selected_employee_index < 0:
            self.selected_employee_index = 0

        if self.selected_employee_index >= employee_count:
            if employee_count > 0:
                self.selected_employee_index = employee_count - 1
            else:
                self.selected_employee_index = 0

    def _player_is_near_kanban(self) -> bool:
        center_x = self.player.x + self.player.width // 2
        center_y = self.player.y + self.player.height // 2
        grid_x = center_x // TILE_SIZE
        grid_y = center_y // TILE_SIZE

        for y in range(grid_y - 1, grid_y + 2):
            for x in range(grid_x - 1, grid_x + 2):
                if 0 <= x < self.office_map.width and 0 <= y < self.office_map.height:
                    if self.office_map.grid[y][x] == OfficeMapModel.KANBAN:
                        return True
        return False
