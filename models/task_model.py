from __future__ import annotations

from dataclasses import dataclass


TASK_STATUS_TODO = "todo"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_DONE = "done"
TASK_STATUS_FAILED = "failed"

ACTIVE_TASK_STATUSES = {TASK_STATUS_TODO, TASK_STATUS_IN_PROGRESS}
FINISHED_TASK_STATUSES = {TASK_STATUS_DONE, TASK_STATUS_FAILED}


@dataclass
class Task:
    id: int
    title: str
    required_skill: str
    difficulty: int
    deadline: float
    business_value: int
    estimated_time: float
    status: str = TASK_STATUS_TODO
    progress: float = 0.0
    assigned_employee: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_TASK_STATUSES

    @property
    def is_finished(self) -> bool:
        return self.status in FINISHED_TASK_STATUSES
