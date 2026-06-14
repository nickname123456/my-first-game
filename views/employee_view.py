import pygame

from models.employee_model import EmployeeModel
from settings import COLORS


class EmployeeView:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 20)

    def draw(self, surface, employees: list[EmployeeModel]) -> None:
        for employee in employees:
            rect = pygame.Rect(*employee.rect)
            pygame.draw.rect(surface, employee.color, rect)
            pygame.draw.rect(surface, COLORS["player_outline"], rect, 2)

            label = self.font.render(employee.role, True, COLORS["text"])
            label_rect = label.get_rect(center=(rect.centerx, rect.top - 8))
            surface.blit(label, label_rect)
