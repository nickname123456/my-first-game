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
from models.notification_model import NOTIFICATION_DANGER, NOTIFICATION_INFO, NotificationModel
from models.project_stats_model import ProjectStatsModel
from models.task_model import (
    TASK_STATUS_DONE,
    TASK_STATUS_FAILED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_QUEUED,
    TASK_STATUS_TODO,
    Task,
)


MAX_ASSIGNMENTS_PER_EMPLOYEE = 3
WORK_FATIGUE_PER_SECOND = 1.15
QUEUE_FATIGUE_PER_TASK_PER_SECOND = 0.25
MIN_FATIGUE_PROGRESS_MULTIPLIER = 0.65
DEADLINE_ESTIMATE_MULTIPLIER = 2.4
DEADLINE_TRAVEL_BUFFER = 28.0
MISMATCH_TECH_DEBT_DRIFT_PER_SECOND = 0.45


@dataclass(frozen=True)
class TaskTemplate:
    title: str
    required_skill: str
    difficulty: int
    deadline_offset: float
    business_value: int
    estimated_time: float


@dataclass(frozen=True)
class TaskCounters:
    new_count: int = 0
    active_count: int = 0
    successful_count: int = 0
    overdue_count: int = 0


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
        self._tech_debt_drift = 0.0
        self.notifications: list[NotificationModel] = []

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
            task = self.spawn_task(current_time)
            if task is not None:
                self._notify_new_task(task)

        self._fail_overdue_tasks(current_time, employees, stats)
        self._update_in_progress_tasks(dt, employees, stats)
        self.sync_stats(stats)

    def consume_notifications(self) -> list[NotificationModel]:
        notifications = self.notifications[:]
        self.notifications.clear()
        return notifications

    def task_counters(self) -> TaskCounters:
        new_count = 0
        active_count = 0
        successful_count = 0
        overdue_count = 0

        for task in self.tasks:
            if task.status == TASK_STATUS_TODO:
                new_count += 1
            elif task.status in (TASK_STATUS_QUEUED, TASK_STATUS_IN_PROGRESS):
                active_count += 1
            elif task.status == TASK_STATUS_DONE:
                successful_count += 1
            elif task.status == TASK_STATUS_FAILED:
                overdue_count += 1

        return TaskCounters(
            new_count=new_count,
            active_count=active_count,
            successful_count=successful_count,
            overdue_count=overdue_count,
        )

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
            deadline=current_time + max(
                template.deadline_offset,
                template.estimated_time * DEADLINE_ESTIMATE_MULTIPLIER
                + DEADLINE_TRAVEL_BUFFER,
            ),
            business_value=template.business_value,
            estimated_time=template.estimated_time,
        )
        self._next_task_id += 1
        self.tasks.append(task)
        return task

    def _notify_new_task(self, task: Task) -> None:
        self.notifications.append(
            NotificationModel(
                f"Новая задача: {task.title} | {task.required_skill} | срок {int(task.deadline)}с",
                severity=NOTIFICATION_INFO,
            )
        )

    def assign_task(self, task_id: int, employee: EmployeeModel) -> bool:
        task = self.get_task(task_id)
        if task is None or task.status != TASK_STATUS_TODO:
            return False

        if not self.employee_has_capacity(employee):
            return False

        task.assigned_employee = employee.name
        if employee.current_task_id is None:
            self._start_task_for_employee(task, employee)
        else:
            task.status = TASK_STATUS_QUEUED
            employee.task_queue.append(task.id)

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

    def available_tasks(self) -> list[Task]:
        available_tasks = []

        for task in self.tasks:
            if task.status == TASK_STATUS_TODO:
                available_tasks.append(task)

        return available_tasks

    def employee_has_capacity(self, employee: EmployeeModel) -> bool:
        return employee.assignment_count < MAX_ASSIGNMENTS_PER_EMPLOYEE

    def calculate_employee_load(
        self,
        employee: EmployeeModel,
        current_time: float,
    ) -> float:
        task_ids = self.employee_task_ids(employee)
        load = employee.fatigue * 0.55
        load += len(task_ids) * 10.0
        load += max(0, len(task_ids) - 1) * 22.0

        if employee.active_crisis_id is not None:
            load += 16.0

        for task_id in task_ids:
            task = self.get_task(task_id)
            if task is None:
                continue

            load += task.difficulty * 2.0
            if task.required_skill != employee.role:
                load += 18.0

            time_left = task.deadline - current_time
            if time_left <= task.estimated_time * 1.2:
                load += 14.0
            if time_left <= 10.0:
                load += 10.0

        return max(0.0, min(100.0, load))

    def employee_has_deadline_pressure(
        self,
        employee: EmployeeModel,
        current_time: float,
    ) -> bool:
        for task_id in self.employee_task_ids(employee):
            task = self.get_task(task_id)
            if task is None:
                continue
            if task.deadline - current_time <= max(10.0, task.estimated_time * 1.2):
                return True
        return False

    def employee_task_ids(self, employee: EmployeeModel) -> list[int]:
        task_ids = []
        if employee.current_task_id is not None:
            task_ids.append(employee.current_task_id)
        task_ids.extend(employee.task_queue)
        return task_ids

    def pop_last_queued_task(self, employee: EmployeeModel) -> Task | None:
        if not employee.task_queue:
            return None

        task_id = employee.task_queue.pop()
        task = self.get_task(task_id)
        if task is None:
            return None

        task.status = TASK_STATUS_TODO
        task.assigned_employee = None
        return task

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

    def sorted_available_tasks(self, current_time: float) -> list[Task]:
        heap: list[tuple[float, int, Task]] = []
        for task in self.available_tasks():
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
        stats: ProjectStatsModel,
    ) -> None:
        for employee in employees:
            if employee.current_task_id is None:
                self._promote_next_task(employee)
                continue

            task = self.get_task(employee.current_task_id)
            if task is None or task.status != TASK_STATUS_IN_PROGRESS:
                self._release_employee(employee)
                continue

            if employee.state != EMPLOYEE_STATE_WORKING or not employee.ready_to_work:
                continue

            speed_multiplier = max(MIN_FATIGUE_PROGRESS_MULTIPLIER, 1.0 - employee.fatigue / 130.0)
            progress_delta = employee.task_progress_speed * speed_multiplier * dt
            task.progress = min(100.0, task.progress + progress_delta)
            employee.fatigue = min(100.0, employee.fatigue + WORK_FATIGUE_PER_SECOND * dt)
            if len(employee.task_queue) > 0:
                employee.fatigue = min(
                    100.0,
                    employee.fatigue + QUEUE_FATIGUE_PER_TASK_PER_SECOND * len(employee.task_queue) * dt,
                )

            if task.required_skill != employee.role:
                self._tech_debt_drift += MISMATCH_TECH_DEBT_DRIFT_PER_SECOND * dt
                if self._tech_debt_drift >= 1.0:
                    gained_debt = int(self._tech_debt_drift)
                    self._tech_debt_drift -= gained_debt
                    stats.apply_changes(tech_debt=gained_debt)

            if task.progress >= 100.0:
                task.status = TASK_STATUS_DONE
                employee.success_boost_timer = 12.0
                if task.required_skill == employee.role:
                    stats.apply_changes(quality=1, morale=1)
                else:
                    stats.apply_changes(
                        morale=-2,
                        quality=-5,
                        tech_debt=8,
                        client_trust=-3,
                    )
                self._release_employee(employee)



    def _fail_overdue_tasks(
        self,
        current_time: float,
        employees: list[EmployeeModel],
        stats: ProjectStatsModel,
    ) -> None:
        for task in self.tasks:
            if task.is_active and current_time > task.deadline:
                task.status = TASK_STATUS_FAILED
                task.progress = min(task.progress, 99.0)
                self._apply_overdue_penalty(task, stats)
                assigned = self._find_employee_by_task(task.id, employees)
                if assigned is not None:
                    if assigned.current_task_id == task.id:
                        self._release_employee(assigned)
                    elif task.id in assigned.task_queue:
                        assigned.task_queue.remove(task.id)

    def _apply_overdue_penalty(self, task: Task, stats: ProjectStatsModel) -> None:
        budget = -2
        morale = -(3 + task.difficulty // 2)
        quality = -(2 + task.difficulty // 2)
        tech_debt = max(1, task.difficulty // 2)
        client_trust = -(5 + task.business_value // 2)
        stats.apply_changes(
            budget=budget,
            morale=morale,
            quality=quality,
            tech_debt=tech_debt,
            client_trust=client_trust,
        )
        self.notifications.append(
            NotificationModel(
                (
                    f"Просрочена задача: {task.title}. "
                    f"Бюджет {budget}, мораль {morale}, качество {quality}, "
                    f"долг +{tech_debt}, доверие {client_trust}"
                ),
                severity=NOTIFICATION_DANGER,
            )
        )



    def _find_employee_by_task(self, task_id: int, employees: list[EmployeeModel]) -> EmployeeModel | None:
        for employee in employees:
            if employee.current_task_id == task_id or task_id in employee.task_queue:
                return employee

        return None

    def _calculate_progress_speed(self, task: Task, employee: EmployeeModel) -> float:
        skill_multiplier = 1.0 if task.required_skill == employee.role else 0.55
        return 100.0 / max(1.0, task.estimated_time) * skill_multiplier

    def _start_task_for_employee(self, task: Task, employee: EmployeeModel) -> None:
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

    def _promote_next_task(self, employee: EmployeeModel) -> None:
        while employee.current_task_id is None and employee.task_queue:
            next_task_id = employee.task_queue.pop(0)
            task = self.get_task(next_task_id)
            if task is None or task.status != TASK_STATUS_QUEUED:
                continue
            self._start_task_for_employee(task, employee)

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
        self._promote_next_task(employee)

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
