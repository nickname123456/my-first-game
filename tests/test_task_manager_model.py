from models.employee_model import EMPLOYEE_STATE_WORKING, EmployeeModel
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import (
    TASK_STATUS_DONE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_QUEUED,
    TASK_STATUS_TODO,
    Task,
)
from settings import CHARACTER_HITBOX_HEIGHT, CHARACTER_HITBOX_WIDTH


def make_task(
    task_id: int,
    deadline: float,
    business_value: int = 5,
    estimated_time: float = 10,
    status: str = TASK_STATUS_TODO,
    required_skill: str = "backend",
) -> Task:
    return Task(
        id=task_id,
        title=f"Task {task_id}",
        required_skill=required_skill,
        difficulty=3,
        deadline=deadline,
        business_value=business_value,
        estimated_time=estimated_time,
        status=status,
    )


def make_employee() -> EmployeeModel:
    return EmployeeModel(
        "Anton",
        "backend",
        0,
        0,
        CHARACTER_HITBOX_WIDTH,
        CHARACTER_HITBOX_HEIGHT,
    )


def spawn_all_tasks(manager: TaskManager) -> None:
    while manager.spawn_task(current_time=0.0) is not None:
        pass


def test_priority_queue_ranks_urgent_task_higher_than_non_urgent() -> None:
    manager = TaskManager(initial_tasks=0)
    urgent = make_task(1, deadline=12)
    later = make_task(2, deadline=80)

    assert manager.calculate_task_priority(urgent, 0) > manager.calculate_task_priority(later, 0)


def test_priority_queue_ranks_more_valuable_task_higher_with_equal_deadline() -> None:
    manager = TaskManager(initial_tasks=0)
    low_value = make_task(1, deadline=40, business_value=3)
    high_value = make_task(2, deadline=40, business_value=9)

    assert manager.calculate_task_priority(high_value, 0) > manager.calculate_task_priority(low_value, 0)


def test_assign_task_marks_task_in_progress_and_employee_busy() -> None:
    manager = TaskManager(initial_tasks=0)
    employee = make_employee()
    manager.tasks = [make_task(1, deadline=40)]

    assert manager.assign_task(1, employee) is True
    assert manager.tasks[0].status == TASK_STATUS_IN_PROGRESS
    assert employee.is_busy is True
    assert employee.current_task_id == 1


def test_assign_task_queues_when_employee_already_has_current_task() -> None:
    manager = TaskManager(initial_tasks=0)
    employee = make_employee()
    manager.tasks = [make_task(1, deadline=40), make_task(2, deadline=60)]

    assert manager.assign_task(1, employee) is True
    assert manager.assign_task(2, employee) is True
    assert manager.tasks[1].status == TASK_STATUS_QUEUED
    assert employee.task_queue == [2]


def test_assign_task_rejects_employee_with_full_queue() -> None:
    manager = TaskManager(initial_tasks=0)
    employee = make_employee()
    manager.tasks = [
        make_task(1, deadline=40),
        make_task(2, deadline=60),
        make_task(3, deadline=80),
        make_task(4, deadline=90),
    ]

    assert manager.assign_task(1, employee) is True
    assert manager.assign_task(2, employee) is True
    assert manager.assign_task(3, employee) is True
    assert manager.assign_task(4, employee) is False
    assert manager.tasks[3].status == TASK_STATUS_TODO
    assert employee.task_queue == [2, 3]


def test_queued_task_is_promoted_after_current_task_is_done() -> None:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = make_employee()
    stats = ProjectStatsModel()
    manager.tasks = [
        make_task(1, deadline=40, estimated_time=1),
        make_task(2, deadline=60, estimated_time=10),
    ]
    manager.assign_task(1, employee)
    manager.assign_task(2, employee)
    employee.state = EMPLOYEE_STATE_WORKING
    employee.ready_to_work = True

    manager.update(2.0, [employee], stats)

    assert manager.tasks[0].status == TASK_STATUS_DONE
    assert manager.tasks[1].status == TASK_STATUS_IN_PROGRESS
    assert employee.current_task_id == 2
    assert employee.task_queue == []


def test_early_release_is_blocked_until_full_task_pool_spawned() -> None:
    manager = TaskManager(initial_tasks=0)
    manager.spawn_task(current_time=0.0)
    manager.tasks[0].status = TASK_STATUS_DONE

    assert manager.can_release_early() is False


def test_early_release_is_available_when_full_pool_is_finished() -> None:
    manager = TaskManager(initial_tasks=0)
    spawn_all_tasks(manager)
    for task in manager.tasks:
        task.status = TASK_STATUS_DONE

    assert manager.spawned_all_tasks() is True
    assert manager.all_spawned_tasks_finished() is True
    assert manager.can_release_early() is True
