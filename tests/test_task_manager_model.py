from models.employee_model import EmployeeModel
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_IN_PROGRESS, Task


def make_task(
    task_id: int,
    deadline: float,
    business_value: int = 5,
    estimated_time: float = 10,
    status: str = "todo",
) -> Task:
    return Task(
        id=task_id,
        title=f"Task {task_id}",
        required_skill="backend",
        difficulty=3,
        deadline=deadline,
        business_value=business_value,
        estimated_time=estimated_time,
        status=status,
    )


def make_employee() -> EmployeeModel:
    return EmployeeModel("Anton", "backend", 0, 0, 20, 20)


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


def test_completed_task_is_not_returned_as_active() -> None:
    manager = TaskManager(initial_tasks=0)
    manager.tasks = [
        make_task(1, deadline=40),
        make_task(2, deadline=40, status=TASK_STATUS_DONE),
    ]

    assert [task.id for task in manager.sorted_active_tasks(0)] == [1]


def test_assign_task_marks_task_in_progress_and_employee_busy() -> None:
    manager = TaskManager(initial_tasks=0)
    employee = make_employee()
    manager.tasks = [make_task(1, deadline=40)]

    assert manager.assign_task(1, employee) is True
    assert manager.tasks[0].status == TASK_STATUS_IN_PROGRESS
    assert employee.is_busy is True
    assert employee.current_task_id == 1


def test_task_progress_increases_during_update() -> None:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = make_employee()
    stats = ProjectStatsModel()
    manager.tasks = [make_task(1, deadline=40, estimated_time=10)]
    manager.assign_task(1, employee)

    manager.update(1.0, [employee], stats)

    assert manager.tasks[0].progress > 0


def test_overdue_unfinished_task_becomes_failed() -> None:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = make_employee()
    stats = ProjectStatsModel(release_time_left=178.0)
    manager.tasks = [make_task(1, deadline=1)]
    manager.assign_task(1, employee)

    manager.update(0.1, [employee], stats)

    assert manager.tasks[0].status == TASK_STATUS_FAILED
    assert employee.is_busy is False
