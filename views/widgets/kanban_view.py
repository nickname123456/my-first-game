import pygame

from models.entities.employee_model import EmployeeModel
from models.systems.task_manager_model import MAX_ASSIGNMENTS_PER_EMPLOYEE, TaskCounters
from models.entities.task_model import TASK_STATUS_TODO, Task
from settings import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from views.shared.font_utils import get_ui_font


class KanbanView:
    def __init__(self) -> None:
        self.title_font = get_ui_font(28)
        self.font = get_ui_font(20)
        self.small_font = get_ui_font(18)
        self.task_rects: list[pygame.Rect] = []
        self.employee_rects: list[pygame.Rect] = []
        self.assign_rect = pygame.Rect(0, 0, 0, 0)
        self.early_release_rect = pygame.Rect(0, 0, 0, 0)
        self.close_rect = pygame.Rect(0, 0, 0, 0)

    def draw(
        self,
        surface,
        tasks: list[Task],
        employees: list[EmployeeModel],
        selected_task_id: int | None,
        selected_task_index: int,
        selected_employee_index: int,
        task_counters: TaskCounters,
        early_release_available: bool,
    ) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(140, 78, SCREEN_WIDTH - 280, SCREEN_HEIGHT - 156)
        pygame.draw.rect(surface, (42, 47, 55), panel, border_radius=6)
        pygame.draw.rect(surface, COLORS["grid"], panel, 2, border_radius=6)

        self.close_rect = pygame.Rect(panel.right - 42, panel.top + 12, 28, 28)
        self._draw_text(surface, "Канбан-доска", self.title_font, panel.left + 22, panel.top + 16)
        self._draw_text(surface, "X", self.font, self.close_rect.x + 8, self.close_rect.y + 3)
        pygame.draw.rect(surface, COLORS["grid"], self.close_rect, 1, border_radius=4)

        self._draw_task_counters(surface, task_counters, panel.left + 24, panel.top + 58)

        tasks_title_y = panel.top + 98
        self._draw_text(surface, "Задачи по приоритету", self.font, panel.left + 24, tasks_title_y)
        self._draw_text(surface, "Сотрудники", self.font, panel.left + 610, tasks_title_y)

        self.task_rects = self._draw_tasks(
            surface,
            tasks,
            selected_task_id,
            selected_task_index,
            panel.left + 22,
            panel.top + 130,
        )
        selected_task = self._get_selected_task(tasks, selected_task_id)
        self.employee_rects = self._draw_employees(
            surface,
            employees,
            selected_task,
            selected_employee_index,
            panel.left + 610,
            panel.top + 130,
        )

        self.assign_rect = pygame.Rect(panel.left + 610, panel.bottom - 112, 250, 40)
        can_assign = bool(
            selected_task is not None
            and employees
            and selected_task.status == TASK_STATUS_TODO
            and employees[selected_employee_index].assignment_count < MAX_ASSIGNMENTS_PER_EMPLOYEE
        )
        assign_color = (73, 148, 111) if can_assign else (72, 78, 88)
        pygame.draw.rect(surface, assign_color, self.assign_rect, border_radius=4)
        self._draw_text(
            surface,
            "Назначить: Enter",
            self.font,
            self.assign_rect.x + 46,
            self.assign_rect.y + 9,
        )

        self.early_release_rect = pygame.Rect(panel.left + 610, panel.bottom - 64, 250, 40)
        release_color = (73, 148, 111) if early_release_available else (72, 78, 88)
        pygame.draw.rect(surface, release_color, self.early_release_rect, border_radius=4)
        pygame.draw.rect(surface, COLORS["grid"], self.early_release_rect, 1, border_radius=4)
        self._draw_text(
            surface,
            "Досрочный релиз: R",
            self.font,
            self.early_release_rect.x + 28,
            self.early_release_rect.y + 9,
        )

        help_text = "Выберите задачу" if selected_task is None else "Выберите исполнителя"
        self._draw_text(surface, help_text, self.small_font, panel.left + 24, panel.bottom - 38)

    def _draw_task_counters(
        self,
        surface,
        counters: TaskCounters,
        x: int,
        y: int,
    ) -> None:
        badges = [
            ("Новые", counters.new_count, (64, 87, 109)),
            ("Активные", counters.active_count, (82, 92, 145)),
            ("Успешные", counters.successful_count, (54, 91, 72)),
            ("Просроченные", counters.overdue_count, (105, 52, 58)),
        ]

        for index, (label, value, fill) in enumerate(badges):
            rect = pygame.Rect(x + index * 162, y, 150, 28)
            pygame.draw.rect(surface, fill, rect, border_radius=4)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1, border_radius=4)
            self._draw_text(
                surface,
                f"{label}: {value}",
                self.small_font,
                rect.x + 10,
                rect.y + 5,
            )

    def hit_test(self, pos: tuple[int, int]) -> tuple[str | None, int]:
        if self.close_rect.collidepoint(pos):
            return "close", -1
        if self.assign_rect.collidepoint(pos):
            return "assign", -1
        if self.early_release_rect.collidepoint(pos):
            return "early_release", -1
        for index, rect in enumerate(self.task_rects):
            if rect.collidepoint(pos):
                return "task", index
        for index, rect in enumerate(self.employee_rects):
            if rect.collidepoint(pos):
                return "employee", index
        return None, -1

    def _draw_tasks(
        self,
        surface,
        tasks: list[Task],
        selected_task_id: int | None,
        selected_index: int,
        x: int,
        y: int,
    ) -> list[pygame.Rect]:
        rects = []
        if not tasks:
            self._draw_text(surface, "Активных задач пока нет", self.font, x, y)
            return rects

        for index, task in enumerate(tasks[:8]):
            rect = pygame.Rect(x, y + index * 50, 548, 42)
            rects.append(rect)
            is_selected = task.id == selected_task_id
            fill = (54, 62, 73)
            if index == selected_index:
                fill = (62, 73, 88)
            if is_selected:
                fill = (72, 116, 150)
            pygame.draw.rect(surface, fill, rect, border_radius=4)
            border_color = COLORS["accent"] if is_selected else COLORS["grid"]
            border_width = 2 if is_selected else 1
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=4)

            title = f"{task.id}. {task.title}"
            meta = (
                f"{task.required_skill} | сложн.:{task.difficulty} | ценность:{task.business_value} "
                f"| срок:{int(task.deadline)}с | {int(task.progress)}%"
            )
            self._draw_text(surface, title, self.font, rect.x + 10, rect.y + 5)
            self._draw_text(surface, meta, self.small_font, rect.x + 10, rect.y + 25, COLORS["muted_text"])

        return rects

    def _draw_employees(
        self,
        surface,
        employees: list[EmployeeModel],
        selected_task: Task | None,
        selected_index: int,
        x: int,
        y: int,
    ) -> list[pygame.Rect]:
        rects = []
        for index, employee in enumerate(employees):
            rect = pygame.Rect(x, y + index * 50, 250, 42)
            rects.append(rect)
            fill = self._employee_fill(employee, selected_task)
            if index == selected_index:
                fill = tuple(min(channel + 18, 255) for channel in fill)
            pygame.draw.rect(surface, fill, rect, border_radius=4)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1, border_radius=4)

            state = self._employee_state_text(employee, selected_task)
            self._draw_text(surface, f"{employee.name} - {employee.role}", self.font, rect.x + 10, rect.y + 5)
            self._draw_text(surface, state, self.small_font, rect.x + 10, rect.y + 25, COLORS["muted_text"])

        return rects

    def _employee_fill(
        self,
        employee: EmployeeModel,
        selected_task: Task | None,
    ) -> tuple[int, int, int]:
        if employee.is_busy:
            if employee.assignment_count >= MAX_ASSIGNMENTS_PER_EMPLOYEE:
                return (68, 42, 45)
            return (42, 46, 54)
        if selected_task is not None and employee.role == selected_task.required_skill:
            return (54, 91, 72)
        return (54, 62, 73)

    def _employee_state_text(
        self,
        employee: EmployeeModel,
        selected_task: Task | None,
    ) -> str:
        if employee.is_busy:
            if employee.assignment_count >= MAX_ASSIGNMENTS_PER_EMPLOYEE:
                return f"перегружен {employee.assignment_count}/{MAX_ASSIGNMENTS_PER_EMPLOYEE}"
            return f"очередь {employee.assignment_count}/{MAX_ASSIGNMENTS_PER_EMPLOYEE}"
        if selected_task is None:
            return "свободен"
        if employee.role == selected_task.required_skill:
            return "подходит"
        return "можно, но медленнее"

    def _get_selected_task(
        self,
        tasks: list[Task],
        selected_task_id: int | None,
    ) -> Task | None:
        if selected_task_id is None:
            return None
        return next((task for task in tasks if task.id == selected_task_id), None)

    def _draw_text(
        self,
        surface,
        value: str,
        font: pygame.font.Font,
        x: int,
        y: int,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        text = font.render(value, True, color or COLORS["text"])
        surface.blit(text, (x, y))
