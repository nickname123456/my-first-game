from models.employee_model import EmployeeModel
from models.employee_model import EMPLOYEE_STATE_GOING_TO_WORK, EMPLOYEE_STATE_WORKING
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import TASK_STATUS_DONE, TASK_STATUS_FAILED, TASK_STATUS_IN_PROGRESS, Task
from settings import CHARACTER_HITBOX_HEIGHT, CHARACTER_HITBOX_WIDTH


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
    return EmployeeModel(
        "Anton",
        "backend",
        0,
        0,
        CHARACTER_HITBOX_WIDTH,
        CHARACTER_HITBOX_HEIGHT,
    )


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
    employee.state = EMPLOYEE_STATE_WORKING
    employee.ready_to_work = True

    manager.update(1.0, [employee], stats)

    assert manager.tasks[0].progress > 0


def test_task_progress_waits_until_employee_is_working() -> None:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = make_employee()
    stats = ProjectStatsModel()
    manager.tasks = [make_task(1, deadline=40, estimated_time=10)]
    manager.assign_task(1, employee)
    employee.state = EMPLOYEE_STATE_GOING_TO_WORK
    employee.ready_to_work = False

    manager.update(1.0, [employee], stats)

    assert manager.tasks[0].progress == 0


def test_fatigue_reduces_task_progress_speed() -> None:
    low_fatigue_manager = TaskManager(initial_tasks=0, spawn_interval=999)
    high_fatigue_manager = TaskManager(initial_tasks=0, spawn_interval=999)
    low_fatigue_employee = make_employee()
    high_fatigue_employee = make_employee()
    stats = ProjectStatsModel()
    low_fatigue_manager.tasks = [make_task(1, deadline=40, estimated_time=10)]
    high_fatigue_manager.tasks = [make_task(1, deadline=40, estimated_time=10)]

    low_fatigue_manager.assign_task(1, low_fatigue_employee)
    high_fatigue_manager.assign_task(1, high_fatigue_employee)
    low_fatigue_employee.state = EMPLOYEE_STATE_WORKING
    low_fatigue_employee.ready_to_work = True
    high_fatigue_employee.state = EMPLOYEE_STATE_WORKING
    high_fatigue_employee.ready_to_work = True
    high_fatigue_employee.fatigue = 80.0

    low_fatigue_manager.update(1.0, [low_fatigue_employee], stats)
    high_fatigue_manager.update(1.0, [high_fatigue_employee], stats)

    assert high_fatigue_manager.tasks[0].progress < low_fatigue_manager.tasks[0].progress


def test_overdue_unfinished_task_becomes_failed() -> None:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = make_employee()
    stats = ProjectStatsModel(release_time_left=178.0)
    manager.tasks = [make_task(1, deadline=1)]
    manager.assign_task(1, employee)

    manager.update(0.1, [employee], stats)

    assert manager.tasks[0].status == TASK_STATUS_FAILED
    assert employee.is_busy is False
