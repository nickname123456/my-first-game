from __future__ import annotations

import heapq
from dataclasses import dataclass

from models.employee_model import (
    EMPLOYEE_STATE_BURNOUT,
    EMPLOYEE_STATE_IDLE,
    EMPLOYEE_STATE_NEEDS_HELP,
    EMPLOYEE_STATE_RESTING,
    EMPLOYEE_STATE_WORKING,
    EmployeeModel,
)
from models.project_stats_model import ProjectStatsModel
from models.task_model import (
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_TODO,
    Task,
)


@dataclass(frozen=True)
class TaskTemplate:
    title: str
    required_skill: str
    difficulty: int
    deadline_offset: float
    business_value: int
    estimated_time: float


class TaskManager:
    def __init__(
        self,
        release_duration: float = 180.0,
        spawn_interval: float = 12.0,
        initial_tasks: int = 3,
    ) -> None:
        self.release_duration = release_duration
        self.spawn_interval = spawn_interval
        self.spawn_timer = 0.0
        self.tasks: list[Task] = []
        self._next_task_id = 1
        self._next_template_index = 0
        self._task_pool = self._build_task_pool()

        for _ in range(initial_tasks):
            self.spawn_task(current_time=0.0)

    def update(
        self,
        dt: float,
        employees: list[EmployeeModel],
        stats: ProjectStatsModel,
    ) -> None:
        current_time = self.elapsed_time(stats)
        self.spawn_timer += dt

        while self.spawn_timer >= self.spawn_interval:
            self.spawn_timer -= self.spawn_interval
            self.spawn_task(current_time)

        self._fail_overdue_tasks(current_time, employees)
        self._update_in_progress_tasks(dt, employees)
        self.sync_stats(stats)

    def elapsed_time(self, stats: ProjectStatsModel) -> float:
        return self.release_duration - stats.release_time_left

    def spawn_task(self, current_time: float) -> Task | None:
        if self._next_template_index >= len(self._task_pool):
            return None

        template = self._task_pool[self._next_template_index]
        self._next_template_index += 1

        task = Task(
            id=self._next_task_id,
            title=template.title,
            required_skill=template.required_skill,
            difficulty=template.difficulty,
            deadline=current_time + template.deadline_offset,
            business_value=template.business_value,
            estimated_time=template.estimated_time,
        )
        self._next_task_id += 1
        self.tasks.append(task)
        return task

    def assign_task(self, task_id: int, employee: EmployeeModel) -> bool:
        task = self.get_task(task_id)
        if task is None or task.status != TASK_STATUS_TODO or employee.is_busy:
            return False

        task.status = TASK_STATUS_IN_PROGRESS
        task.assigned_employee = employee.name
        employee.current_task_id = task.id
        employee.task_progress_speed = self._calculate_progress_speed(task, employee)
        employee.task_picked_up = False
        employee.ready_to_work = False
        employee.state = EMPLOYEE_STATE_IDLE
        employee.target_cell = None
        employee.path = []
        employee.path_index = 0
        return True

    def get_task(self, task_id: int) -> Task | None:
        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    def active_tasks(self) -> list[Task]:
        active_tasks = []

        for task in self.tasks:
            if task.is_active:
                active_tasks.append(task)

        return active_tasks

    def sorted_active_tasks(self, current_time: float) -> list[Task]:
        heap: list[tuple[float, int, Task]] = [] # список из (-priority, task.id, task)
        for task in self.active_tasks():
            priority = self.calculate_task_priority(task, current_time)
            heapq.heappush(heap, (-priority, task.id, task))
        
        result = []

        while heap:
            item = heapq.heappop(heap)
            result.append(item[2])

        return result

    def calculate_task_priority(self, task: Task, current_time: float) -> float:
        time_left = max(1.0, task.deadline - current_time)
        urgency = 100.0 / time_left
        deadline_risk = max(0.0, task.estimated_time - time_left) * 8.0
        value_score = task.business_value * 2.0
        difficulty_score = task.difficulty * 8.0
        duration_penalty = task.estimated_time * 1.5
        return urgency * 3.0 + deadline_risk + value_score + difficulty_score - duration_penalty



    def completed_count(self) -> int:
        count = 0

        for task in self.tasks:
            if task.status == TASK_STATUS_DONE:
                count += 1

        return count



    def failed_count(self) -> int:
        count = 0

        for task in self.tasks:
            if task.status == TASK_STATUS_FAILED:
                count += 1

        return count


    def sync_stats(self, stats: ProjectStatsModel) -> None:
        stats.tasks_done = self.completed_count()
        stats.tasks_failed = self.failed_count()
        stats.tasks_active = len(self.active_tasks())




    def _update_in_progress_tasks(
        self,
        dt: float,
        employees: list[EmployeeModel],
    ) -> None:
        for employee in employees:
            if employee.current_task_id is None:
                continue

            task = self.get_task(employee.current_task_id)
            if task is None or task.status != TASK_STATUS_IN_PROGRESS:
                self._release_employee(employee)
                continue

            if employee.state != EMPLOYEE_STATE_WORKING or not employee.ready_to_work:
                continue

            speed_multiplier = max(0.40, 1.0 - employee.fatigue / 130.0)
            progress_delta = employee.task_progress_speed * speed_multiplier * dt
            task.progress = min(100.0, task.progress + progress_delta)
            employee.fatigue = min(100.0, employee.fatigue + 3.5 * dt)
            if task.progress >= 100.0:
                task.status = TASK_STATUS_DONE
                self._release_employee(employee)



    def _fail_overdue_tasks(
        self,
        current_time: float,
        employees: list[EmployeeModel],
    ) -> None:
        for task in self.tasks:
            if task.is_active and current_time > task.deadline:
                task.status = TASK_STATUS_FAILED
                task.progress = min(task.progress, 99.0)
                assigned = self._find_employee_by_task(task.id, employees)
                if assigned is not None:
                    self._release_employee(assigned)



    def _find_employee_by_task(self, task_id: int, employees: list[EmployeeModel]) -> EmployeeModel | None:
        for employee in employees:
            if employee.current_task_id == task_id:
                return employee

        return None

    def _calculate_progress_speed(self, task: Task, employee: EmployeeModel) -> float:
        skill_multiplier = 1.0 if task.required_skill == employee.role else 0.55
        return 100.0 / max(1.0, task.estimated_time) * skill_multiplier

    def _release_employee(self, employee: EmployeeModel) -> None:
        employee.current_task_id = None
        employee.task_progress_speed = 0.0
        employee.task_picked_up = False
        employee.ready_to_work = False
        employee.target_cell = None
        employee.path = []
        employee.path_index = 0
        if employee.state not in (
            EMPLOYEE_STATE_BURNOUT,
            EMPLOYEE_STATE_NEEDS_HELP,
            EMPLOYEE_STATE_RESTING,
        ):
            employee.state = EMPLOYEE_STATE_IDLE

    def _build_task_pool(self) -> list[TaskTemplate]:
        return [
            TaskTemplate("Сделать API авторизации", "backend", 5, 45, 9, 18),
            TaskTemplate("Сверстать экран задач", "frontend", 4, 40, 8, 16),
            TaskTemplate("Проверить релизный сценарий", "QA", 3, 35, 7, 14),
            TaskTemplate("Настроить деплой", "DevOps", 5, 55, 9, 20),
            TaskTemplate("Добавить рекомендации AI", "AI", 4, 60, 8, 18),
            TaskTemplate("Оптимизировать запросы", "backend", 4, 50, 7, 17),
            TaskTemplate("Починить адаптивность HUD", "frontend", 3, 42, 6, 13),
            TaskTemplate("Написать smoke-тесты", "QA", 4, 48, 8, 16),
            TaskTemplate("Собрать staging-окружение", "DevOps", 3, 52, 7, 15),
            TaskTemplate("Обучить модель подсказок", "AI", 5, 65, 10, 22),
            TaskTemplate("Закрыть баг с сохранением", "backend", 5, 38, 9, 15),
            TaskTemplate("Улучшить окно канбана", "frontend", 2, 44, 6, 12),
        ]
