from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmployeeModel:
    name: str
    role: str
    x: int
    y: int
    width: int
    height: int
    current_task_id: int | None = None
    task_progress_speed: float = 0.0

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    @property
    def is_busy(self) -> bool:
        return self.current_task_id is not None
