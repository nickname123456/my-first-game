from models.crisis_model import (
    CRISIS_BURNOUT,
    CRISIS_CRITICAL_BUG,
    CRISIS_DEFINITIONS,
    CrisisManager,
    describe_effect,
)
from models.employee_model import EmployeeModel
from models.mood_model import MOOD_BURNOUT
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import TASK_STATUS_TODO, Task
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


def make_task(
    task_id: int = 1,
    required_skill: str = "backend",
    deadline: float = 40.0,
) -> Task:
    return Task(
        id=task_id,
        title=f"Task {task_id}",
        required_skill=required_skill,
        difficulty=5,
        deadline=deadline,
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


def test_grace_period_blocks_early_crisis_roll() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(
        FixedRandom([0.0]),
        grace_period=25.0,
        min_task_progress_for_crisis=0.0,
    )

    crisis = crisis_manager.roll_for_employee(employee, manager, stats, current_time=10.0)

    assert crisis is None
    assert employee.active_crisis_id is None


def test_active_crisis_limit_blocks_additional_crises() -> None:
    manager, first_employee, stats = make_assigned_context()
    second_employee = make_employee("frontend")
    second_task = make_task(2, required_skill="frontend", deadline=60.0)
    manager.tasks.append(second_task)
    manager.assign_task(second_task.id, second_employee)
    crisis_manager = CrisisManager(
        FixedRandom([0.0, 0.0]),
        grace_period=0.0,
        max_active_crises=1,
        min_task_progress_for_crisis=0.0,
    )

    first_crisis = crisis_manager.roll_for_employee(first_employee, manager, stats, current_time=30.0)
    second_crisis = crisis_manager.roll_for_employee(second_employee, manager, stats, current_time=30.0)

    assert first_crisis is not None
    assert second_crisis is None
    assert len(crisis_manager.active_crises) == 1


def test_low_task_progress_blocks_crisis_roll() -> None:
    manager, employee, stats = make_assigned_context()
    manager.tasks[0].progress = 19.0
    crisis_manager = CrisisManager(
        FixedRandom([0.0]),
        grace_period=0.0,
        min_task_progress_for_crisis=20.0,
    )

    crisis = crisis_manager.roll_for_employee(employee, manager, stats, current_time=30.0)

    assert crisis is None
    assert employee.active_crisis_id is None


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
    assert employee.recent_help_timer > 0.0
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
    assert employee.fatigue == 13
    assert employee.active_crisis_id is None
    assert crisis_manager.get_crisis(crisis.id) is None

    notifications = crisis_manager.consume_notifications()
    assert len(notifications) == 1
    assert "Кризис проигнорирован" in notifications[0].text
    assert "качество -18" in notifications[0].text


def test_bad_crisis_solution_applies_scaled_penalty() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(FixedRandom([0.0]))
    crisis = crisis_manager.create_crisis(CRISIS_CRITICAL_BUG, employee, manager.tasks[0])

    resolved = crisis_manager.resolve_crisis(crisis.id, 3, [employee], manager, stats)

    assert resolved is True
    assert stats.morale == 94
    assert stats.quality == 82
    assert stats.tech_debt == 9
    assert stats.client_trust == 88

    notifications = crisis_manager.consume_notifications()
    assert len(notifications) == 1
    assert "Кризис решен" in notifications[0].text
    assert "качество -18" in notifications[0].text


def test_burnout_solution_can_return_last_queued_task_to_todo() -> None:
    manager, employee, stats = make_assigned_context()
    queued_task = make_task(2, deadline=60.0)
    manager.tasks.append(queued_task)
    manager.assign_task(queued_task.id, employee)
    crisis_manager = CrisisManager(FixedRandom([0.0]))
    crisis = crisis_manager.create_crisis(CRISIS_BURNOUT, employee, manager.tasks[0])

    resolved = crisis_manager.resolve_crisis(crisis.id, 1, [employee], manager, stats)

    assert resolved is True
    assert queued_task.status == TASK_STATUS_TODO
    assert employee.task_queue == []


def test_bad_burnout_advice_can_force_burnout_mood() -> None:
    manager, employee, stats = make_assigned_context()
    crisis_manager = CrisisManager(FixedRandom([0.0]))
    crisis = crisis_manager.create_crisis(CRISIS_BURNOUT, employee, manager.tasks[0])

    crisis_manager.resolve_crisis(crisis.id, 3, [employee], manager, stats)

    assert employee.mood == MOOD_BURNOUT


def test_effect_description_exposes_dialog_values() -> None:
    option = CRISIS_DEFINITIONS[CRISIS_CRITICAL_BUG].options[0]

    description = describe_effect(option.effect)

    assert "бюджет -8" in description
    assert "качество +6" in description
    assert "долг -3" in description
