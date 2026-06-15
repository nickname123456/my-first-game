import pygame

from models.employee_model import (
    EMPLOYEE_STATE_BURNOUT,
    EMPLOYEE_STATE_GOING_TO_KANBAN,
    EMPLOYEE_STATE_GOING_TO_WORK,
    EMPLOYEE_STATE_IDLE,
    EMPLOYEE_STATE_NEEDS_HELP,
    EMPLOYEE_STATE_RESTING,
    EMPLOYEE_STATE_WORKING,
    EmployeeModel,
)
from models.task_manager_model import TaskManager
from settings import COLORS
from views.font_utils import get_ui_font


ROLE_COLORS = {
    "backend": (80, 164, 222),
    "frontend": (222, 134, 80),
    "QA": (122, 190, 95),
    "DevOps": (185, 128, 220),
    "AI": (220, 190, 84),
}

STATE_LABELS = {
    EMPLOYEE_STATE_IDLE: "гуляет",
    EMPLOYEE_STATE_GOING_TO_KANBAN: "к канбану",
    EMPLOYEE_STATE_GOING_TO_WORK: "к месту",
    EMPLOYEE_STATE_WORKING: "работает",
    EMPLOYEE_STATE_RESTING: "отдыхает",
    EMPLOYEE_STATE_NEEDS_HELP: "ждет помощи",
    EMPLOYEE_STATE_BURNOUT: "выгорел",
}


class EmployeeView:
    def __init__(self) -> None:
        self.font = get_ui_font(18)
        self.small_font = get_ui_font(16)

    def draw(
        self,
        surface,
        employees: list[EmployeeModel],
        task_manager: TaskManager | None = None,
    ) -> None:
        for employee in employees:
            rect = pygame.Rect(*employee.rect)
            color = ROLE_COLORS.get(employee.role, COLORS["accent"])
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLORS["player_outline"], rect, 2)

            label = self.font.render(employee.role, True, COLORS["text"])
            label_rect = label.get_rect(center=(rect.centerx, rect.top - 8))
            surface.blit(label, label_rect)

            if task_manager is not None and employee.current_task_id is not None:
                task = task_manager.get_task(employee.current_task_id)
                if task is not None:
                    state_label = STATE_LABELS.get(employee.state, employee.state)
                    progress = self.small_font.render(
                        f"{state_label} {int(task.progress)}%",
                        True,
                        COLORS["text"],
                    )
                    progress_rect = progress.get_rect(center=(rect.centerx, rect.bottom + 9))
                    surface.blit(progress, progress_rect)
            else:
                state_label = STATE_LABELS.get(employee.state, "свободен")
                state = self.small_font.render(state_label, True, COLORS["muted_text"])
                state_rect = state.get_rect(center=(rect.centerx, rect.bottom + 9))
                surface.blit(state, state_rect)
