import pygame

from models.employee_model import EmployeeModel
from settings import COLORS


ROLE_COLORS = {
    "backend": (80, 164, 222),
    "frontend": (222, 134, 80),
    "QA": (122, 190, 95),
    "DevOps": (185, 128, 220),
    "AI": (220, 190, 84),
}


class EmployeeView:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 20)

    def draw(self, surface, employees: list[EmployeeModel]) -> None:
        for employee in employees:
            rect = pygame.Rect(*employee.rect)
            color = ROLE_COLORS.get(employee.role, COLORS["accent"])
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLORS["player_outline"], rect, 2)

            label = self.font.render(employee.role, True, COLORS["text"])
            label_rect = label.get_rect(center=(rect.centerx, rect.top - 8))
            surface.blit(label, label_rect)
