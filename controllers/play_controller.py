import pygame

from controllers.base_scene_controller import BaseSceneController
from models.crisis_model import CrisisManager
from models.employee_behavior_model import EmployeeBehaviorSystem
from controllers.player_controller import PlayerController
from models.employee_model import EmployeeModel
from models.mood_model import MoodSystem
from models.notification_model import NOTIFICATION_WARNING, NotificationModel
from models.office_map_model import OfficeMapModel
from models.player_model import PlayerModel
from models.project_stats_model import ProjectStatsModel
from models.result_model import (
    GameResult,
    build_game_result,
    determine_game_result,
    failure_reason,
    release_failure_reason,
)
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
        self.mood_system = MoodSystem()
        self.crisis_manager = CrisisManager()
        self.project_stats = ProjectStatsModel()
        self.task_manager = TaskManager(
            release_duration=self.project_stats.release_time_left,
        )
        self.task_manager.sync_stats(self.project_stats)
        self.kanban_open = False
        self.selected_task_id: int | None = None
        self.selected_task_index = 0
        self.selected_employee_index = 0
        self.active_crisis_dialog_id: int | None = None
        self.selected_crisis_option_index = 0
        self.notifications: list[NotificationModel] = []
        self.finished = False
        self.final_result: GameResult | None = None
        self.view = PlayView()

    def handle_event(self, event) -> None:
        if self.finished:
            return

        if self.active_crisis_dialog_id is not None:
            self._handle_crisis_dialog_event(event)
            return

        if self.kanban_open:
            self._handle_kanban_event(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game_controller.quit()
            elif event.key == pygame.K_e:
                if self._open_nearby_crisis_dialog():
                    return
                if self._player_is_near_kanban():
                    self._open_kanban()
            elif event.key == pygame.K_r and self._player_is_near_kanban():
                self._try_early_release()

    def update(self, dt: float) -> None:
        if self.finished:
            return

        self.project_stats.release_time_left = max(
            0.0,
            self.project_stats.release_time_left - dt,
        )
        self._update_notifications(dt)
        current_time = self.task_manager.elapsed_time(self.project_stats)
        self.employee_behavior.update(dt, self.employees, self.office_map)
        self.task_manager.update(dt, self.employees, self.project_stats)
        self._consume_model_notifications()
        self.mood_system.update(dt, self.employees, self.task_manager, current_time)
        self.crisis_manager.update(
            dt,
            self.employees,
            self.task_manager,
            self.project_stats,
            current_time,
        )
        self._consume_model_notifications()
        if self.crisis_manager.get_crisis(self.active_crisis_dialog_id) is None:
            self.active_crisis_dialog_id = None
            self.selected_crisis_option_index = 0

        self._check_final_result()
        if self.finished:
            return

        if not self.kanban_open and self.active_crisis_dialog_id is None:
            self.player_controller.handle_input(pygame.key.get_pressed(), dt)

    def draw(self, surface) -> None:
        sorted_tasks = self._sorted_tasks()
        self.view.draw(
            surface,
            self.office_map,
            self.player,
            self.employees,
            self.project_stats,
            self.task_manager,
            self.crisis_manager,
            sorted_tasks,
            self.kanban_open,
            self.selected_task_id,
            self.selected_task_index,
            self.selected_employee_index,
            self.active_crisis_dialog_id,
            self.selected_crisis_option_index,
            self.notifications,
            self.task_manager.task_counters(),
            self._can_early_release(),
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
            elif event.key == pygame.K_r:
                self._try_early_release()

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
            elif hit_type == "early_release":
                self._try_early_release()
            elif hit_type == "close":
                self.kanban_open = False

    def _handle_crisis_dialog_event(self, event) -> None:
        crisis = self.crisis_manager.get_crisis(self.active_crisis_dialog_id)
        if crisis is None:
            self.active_crisis_dialog_id = None
            self.selected_crisis_option_index = 0
            return

        definition = self.crisis_manager.get_definition(crisis)
        option_count = len(definition.options)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active_crisis_dialog_id = None
                self.selected_crisis_option_index = 0
            elif event.key == pygame.K_UP:
                self.selected_crisis_option_index = self._move_selection(
                    self.selected_crisis_option_index,
                    -1,
                    option_count,
                )
            elif event.key == pygame.K_DOWN:
                self.selected_crisis_option_index = self._move_selection(
                    self.selected_crisis_option_index,
                    1,
                    option_count,
                )
            elif event.key == pygame.K_RETURN:
                self._resolve_active_crisis(self.selected_crisis_option_index)
            elif pygame.K_1 <= event.key <= pygame.K_4:
                option_index = event.key - pygame.K_1
                self._resolve_active_crisis(option_index)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit_type, hit_index = self.view.hit_test_crisis_dialog(event.pos)
            if hit_type == "option":
                self._resolve_active_crisis(hit_index)
            elif hit_type == "close":
                self.active_crisis_dialog_id = None
                self.selected_crisis_option_index = 0

    def _create_employees(self) -> list[EmployeeModel]:
        employee_width = CHARACTER_HITBOX_WIDTH
        employee_height = CHARACTER_HITBOX_HEIGHT
        employees = []
        for name, role in (
            ("Яков", "backend"),
            ("Кира", "frontend"),
            ("Шура", "QA"),
            ("Тимур", "DevOps"),
            ("Алик", "AI"),
        ):
            work_cell = self.office_map.workplace_targets[role]
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

    def _resolve_active_crisis(self, option_index: int) -> None:
        if self.active_crisis_dialog_id is None:
            return
        resolved = self.crisis_manager.resolve_crisis(
            self.active_crisis_dialog_id,
            option_index,
            self.employees,
            self.task_manager,
            self.project_stats,
        )
        if resolved:
            self._consume_model_notifications()
            self.active_crisis_dialog_id = None
            self.selected_crisis_option_index = 0

    def _try_early_release(self) -> None:
        self.task_manager.sync_stats(self.project_stats)
        blocker = self._early_release_blocker()
        if blocker is not None:
            self.notifications.append(
                NotificationModel(blocker, severity=NOTIFICATION_WARNING)
            )
            return

        result = build_game_result(
            self.project_stats,
            True,
            "Досрочный релиз успешен: все задачи закрыты до даты релиза",
            getattr(self.game_controller, "high_score_path", None),
            early_release=True,
            release_duration=self.task_manager.release_duration,
        )
        self._finish_game(result)

    def _can_early_release(self) -> bool:
        return self._early_release_blocker() is None

    def _early_release_blocker(self) -> str | None:
        task_blocker = self.task_manager.early_release_blocker()
        if task_blocker is not None:
            return task_blocker

        critical_reason = failure_reason(self.project_stats)
        if critical_reason is not None:
            return f"Досрочный релиз недоступен: {critical_reason}"

        release_blocker = release_failure_reason(self.project_stats)
        if release_blocker is not None:
            return release_blocker

        return None

    def _sorted_tasks(self):
        current_time = self.task_manager.elapsed_time(self.project_stats)
        return self.task_manager.sorted_available_tasks(current_time)

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

    def _open_nearby_crisis_dialog(self) -> bool:
        employee = self._nearby_crisis_employee()
        if employee is None or employee.active_crisis_id is None:
            return False
        if self.crisis_manager.get_crisis(employee.active_crisis_id) is None:
            return False
        self.active_crisis_dialog_id = employee.active_crisis_id
        self.selected_crisis_option_index = 0
        return True

    def _nearby_crisis_employee(self) -> EmployeeModel | None:
        player_rect = pygame.Rect(self.player.rect)
        for employee in self.employees:
            if employee.active_crisis_id is None:
                continue
            employee_rect = pygame.Rect(employee.rect).inflate(80, 80)
            if player_rect.colliderect(employee_rect):
                return employee
        return None

    def _check_final_result(self) -> None:
        result = determine_game_result(
            self.project_stats,
            getattr(self.game_controller, "high_score_path", None),
        )
        if result is not None:
            self._finish_game(result)

    def _finish_game(self, result: GameResult) -> None:
        self.finished = True
        self.final_result = result
        show_result = getattr(self.game_controller, "show_result", None)
        if callable(show_result):
            show_result(result)

    def _consume_model_notifications(self) -> None:
        self.notifications.extend(self.task_manager.consume_notifications())
        self.notifications.extend(self.crisis_manager.consume_notifications())

    def _update_notifications(self, dt: float) -> None:
        active_notifications = []
        for notification in self.notifications:
            notification.time_left -= dt
            if notification.time_left > 0.0:
                active_notifications.append(notification)
        self.notifications = active_notifications
