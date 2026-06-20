from models.systems.crisis_model import CRISIS_CRITICAL_BUG, CRISIS_DEFINITIONS, CrisisManager
from models.entities.employee_model import EmployeeModel
from models.entities.project_stats_model import ProjectStatsModel
from models.systems.task_manager_model import TaskManager
from models.entities.task_model import Task
from settings import CHARACTER_HITBOX_HEIGHT, CHARACTER_HITBOX_WIDTH


class FixedRandom:
    def __init__(self, values: list[float]) -> None:
        self.values = values
        self.index = 0

    def random(self) -> float:
        if self.index >= len(self.values):
            return self.values[-1]
        value = self.values[self.index]
        self.index += 1
        return value


def make_employee(role: str = "backend") -> EmployeeModel:
    return EmployeeModel(
        "Anton",
        role,
        0,
        0,
        CHARACTER_HITBOX_WIDTH,
        CHARACTER_HITBOX_HEIGHT,
    )


def make_task(required_skill: str = "backend") -> Task:
    return Task(
        id=1,
        title="Task 1",
        required_skill=required_skill,
        difficulty=5,
        deadline=40,
        business_value=8,
        estimated_time=12,
    )


def make_assigned_context(
    employee: EmployeeModel | None = None,
    task: Task | None = None,
) -> tuple[TaskManager, EmployeeModel, ProjectStatsModel]:
    manager = TaskManager(initial_tasks=0, spawn_interval=999)
    employee = employee or make_employee()
    task = task or make_task()
    manager.tasks = [task]
    manager.assign_task(task.id, employee)
    return manager, employee, ProjectStatsModel()


def test_prd_increases_failed_roll_counter_after_no_crisis() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(
        FixedRandom([0.99]),
        roll_interval=4.0,
        grace_period=0.0,
        min_task_progress_for_crisis=0.0,
    )

    crisis = crisis_manager.roll_for_employee(employee, manager, stats, current_time=0.0)

    assert crisis is None
    assert crisis_manager.failed_rolls[employee.name] == 1


def test_prd_resets_failed_roll_counter_after_crisis() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(
        FixedRandom([0.0, 0.0]),
        roll_interval=4.0,
        grace_period=0.0,
        min_task_progress_for_crisis=0.0,
    )

    crisis = crisis_manager.roll_for_employee(employee, manager, stats, current_time=0.0)

    assert crisis is not None
    assert crisis_manager.failed_rolls[employee.name] == 0
    assert employee.active_crisis_id == crisis.id


def test_mismatch_skill_increases_crisis_base_chance() -> None:
    matched_manager, matched_employee, matched_stats = make_assigned_context()
    mismatch_employee = make_employee("backend")
    mismatch_task = make_task(required_skill="frontend")
    mismatch_manager, mismatch_employee, mismatch_stats = make_assigned_context(
        mismatch_employee,
        mismatch_task,
    )
    crisis_manager = CrisisManager(FixedRandom([0.99]))

    matched_chance = crisis_manager.calculate_base_chance(
        matched_employee,
        matched_manager.tasks[0],
        matched_manager,
        matched_stats,
        current_time=0.0,
    )
    mismatch_chance = crisis_manager.calculate_base_chance(
        mismatch_employee,
        mismatch_manager.tasks[0],
        mismatch_manager,
        mismatch_stats,
        current_time=0.0,
    )

    assert mismatch_chance > matched_chance


def test_resolving_crisis_applies_effect_once_and_clamps_resources() -> None:
    manager, employee, stats = make_assigned_context()
    stats.budget = 5
    stats.quality = 98
    stats.tech_debt = 1
    employee.fatigue = 98.0
    crisis_manager = CrisisManager(FixedRandom([0.0]))
    crisis = crisis_manager.create_crisis(CRISIS_CRITICAL_BUG, employee, manager.tasks[0])

    resolved = crisis_manager.resolve_crisis(crisis.id, 0, [employee], manager, stats)

    assert resolved is True
    assert stats.budget == 0
    assert stats.quality == 100
    assert stats.tech_debt == 0
    assert employee.fatigue == 100.0
    assert employee.active_crisis_id is None
    assert crisis_manager.get_crisis(crisis.id) is None


def test_crisis_timeout_applies_penalty() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(FixedRandom([0.99]), roll_interval=999)
    crisis = crisis_manager.create_crisis(CRISIS_CRITICAL_BUG, employee, manager.tasks[0])

    crisis_manager.update(
        CRISIS_DEFINITIONS[CRISIS_CRITICAL_BUG].duration + 1.0,
        [employee],
        manager,
        stats,
        current_time=0.0,
    )

    assert stats.morale == 92
    assert stats.quality == 82
    assert stats.tech_debt == 15
    assert employee.active_crisis_id is None
    assert crisis_manager.get_crisis(crisis.id) is None
