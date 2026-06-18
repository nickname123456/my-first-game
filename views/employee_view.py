from pathlib import Path

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
from models.crisis_model import CrisisManager
from models.task_manager_model import TaskManager
from settings import COLORS, PLAYER_SPRITE_SIZE
from views.font_utils import get_ui_font


ROLE_COLORS = {
    "backend": (80, 164, 222),
    "frontend": (222, 134, 80),
    "QA": (122, 190, 95),
    "DevOps": (185, 128, 220),
    "AI": (220, 190, 84),
}

ROLE_SPRITE_FOLDERS = {
    "backend": "backend",
    "frontend": "frontend",
    "QA": "tester",
    "DevOps": "devops",
    "AI": "ai",
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
    FRAME_COLUMNS = 3
    FRAME_ROWS = 4
    FRAME_WIDTH = 64
    FRAME_HEIGHT = 64
    DRAW_SIZE = PLAYER_SPRITE_SIZE
    WALK_FPS = 8
    IDLE_FRAME = 1
    SPRITES_ROOT = Path(__file__).resolve().parent.parent / "assets" / "sprites"
    DIRECTION_ROWS = {
        "down": 0,
        "left": 1,
        "right": 2,
        "up": 3,
    }

    def __init__(self) -> None:
        self.font = get_ui_font(18)
        self.small_font = get_ui_font(16)
        self.frames_by_role = self._load_role_frames()

    def draw(
        self,
        surface,
        employees: list[EmployeeModel],
        task_manager: TaskManager | None = None,
        crisis_manager: CrisisManager | None = None,
    ) -> None:
        for employee in employees:
            rect = pygame.Rect(*employee.rect)
            visual_rect = self._draw_employee(surface, employee, rect)
            self._draw_crisis_indicator(surface, employee, visual_rect, crisis_manager)

            label = self.font.render(employee.role, True, COLORS["text"])
            label_rect = label.get_rect(center=(rect.centerx, visual_rect.top - 8))
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

    def _load_role_frames(self) -> dict[str, dict[str, list[pygame.Surface]] | None]:
        frames_by_role: dict[str, dict[str, list[pygame.Surface]] | None] = {}
        for role, folder in ROLE_SPRITE_FOLDERS.items():
            path = self.SPRITES_ROOT / folder / "walk.png"
            frames_by_role[role] = self._load_frames(path)
        return frames_by_role

    def _load_frames(self, path: Path) -> dict[str, list[pygame.Surface]] | None:
        try:
            spritesheet = pygame.image.load(str(path)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

        frames: dict[str, list[pygame.Surface]] = {}
        for direction, row in self.DIRECTION_ROWS.items():
            frames[direction] = []
            for column in range(self.FRAME_COLUMNS):
                frame_rect = pygame.Rect(
                    column * self.FRAME_WIDTH,
                    row * self.FRAME_HEIGHT,
                    self.FRAME_WIDTH,
                    self.FRAME_HEIGHT,
                )
                frame = spritesheet.subsurface(frame_rect).copy()
                scaled_frame = pygame.transform.scale(
                    frame,
                    (self.DRAW_SIZE, self.DRAW_SIZE),
                )
                frames[direction].append(scaled_frame)
        return frames

    def _draw_employee(
        self,
        surface,
        employee: EmployeeModel,
        hitbox: pygame.Rect,
    ) -> pygame.Rect:
        frames = self.frames_by_role.get(employee.role)
        if frames is None:
            return self._draw_fallback(surface, employee, hitbox)

        direction_frames = frames.get(employee.direction)
        if direction_frames is None:
            direction_frames = frames["down"]

        if employee.is_moving:
            frame_index = int(employee.animation_time * self.WALK_FPS) % self.FRAME_COLUMNS
        else:
            frame_index = self.IDLE_FRAME

        image = direction_frames[frame_index]
        draw_rect = self._sprite_rect_for_hitbox(hitbox)
        surface.blit(image, draw_rect)
        return draw_rect

    def _draw_fallback(
        self,
        surface,
        employee: EmployeeModel,
        hitbox: pygame.Rect,
    ) -> pygame.Rect:
        color = ROLE_COLORS.get(employee.role, COLORS["accent"])
        pygame.draw.rect(surface, color, hitbox)
        pygame.draw.rect(surface, COLORS["player_outline"], hitbox, 2)
        return hitbox

    def _sprite_rect_for_hitbox(self, hitbox: pygame.Rect) -> pygame.Rect:
        rect = pygame.Rect(0, 0, self.DRAW_SIZE, self.DRAW_SIZE)
        rect.midbottom = hitbox.midbottom
        return rect

    def _draw_crisis_indicator(
        self,
        surface,
        employee: EmployeeModel,
        visual_rect: pygame.Rect,
        crisis_manager: CrisisManager | None,
    ) -> None:
        if crisis_manager is None or employee.active_crisis_id is None:
            return

        crisis = crisis_manager.get_crisis(employee.active_crisis_id)
        if crisis is None:
            return

        center = (visual_rect.centerx + 26, visual_rect.top - 26)
        pygame.draw.circle(surface, (214, 68, 68), center, 16)
        pygame.draw.circle(surface, COLORS["player_outline"], center, 16, 2)

        marker = self.font.render("!", True, COLORS["text"])
        marker_rect = marker.get_rect(center=(center[0], center[1] - 2))
        surface.blit(marker, marker_rect)

        timer = self.small_font.render(str(max(0, int(crisis.time_left))), True, COLORS["text"])
        timer_rect = timer.get_rect(center=(center[0], center[1] + 22))
        surface.blit(timer, timer_rect)
