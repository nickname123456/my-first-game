from __future__ import annotations

from dataclasses import dataclass, field


EMPLOYEE_STATE_IDLE = "idle"
EMPLOYEE_STATE_GOING_TO_KANBAN = "going_to_kanban"
EMPLOYEE_STATE_GOING_TO_WORK = "going_to_work"
EMPLOYEE_STATE_WORKING = "working"
EMPLOYEE_STATE_RESTING = "resting"
EMPLOYEE_STATE_NEEDS_HELP = "needs_help"
EMPLOYEE_STATE_BURNOUT = "burnout"


@dataclass
class EmployeeModel:
    name: str
    role: str
    x: int
    y: int
    width: int
    height: int
    current_task_id: int | None = None
    task_queue: list[int] = field(default_factory=list)
    task_progress_speed: float = 0.0
    state: str = EMPLOYEE_STATE_IDLE
    mood: str = "normal"
    fatigue: float = 0.0
    active_crisis_id: int | None = None
    recent_help_timer: float = 0.0
    success_boost_timer: float = 0.0
    target_cell: tuple[int, int] | None = None
    path: list[tuple[int, int]] | None = None
    path_index: int = 0
    work_cell: tuple[int, int] | None = None
    task_picked_up: bool = False
    ready_to_work: bool = False
    needs_help: bool = False
    direction: str = "down"
    is_moving: bool = False
    animation_time: float = 0.0

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    @property
    def is_busy(self) -> bool:
        return self.current_task_id is not None or bool(self.task_queue)

    @property
    def assignment_count(self) -> int:
        count = len(self.task_queue)
        if self.current_task_id is not None:
            count += 1
        return count

    def set_movement_state(self, direction: str | None, is_moving: bool, dt: float) -> None:
        if direction is not None:
            self.direction = direction

        self.is_moving = is_moving
        if is_moving:
            self.animation_time += dt
        else:
            self.animation_time = 0.0
