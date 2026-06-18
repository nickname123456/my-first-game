from __future__ import annotations

import random
from dataclasses import dataclass

from models.employee_model import (
    EMPLOYEE_STATE_BURNOUT,
    EMPLOYEE_STATE_IDLE,
    EmployeeModel,
)
from models.mood_model import MOOD_BURNOUT, MOOD_STRESSED, MOOD_TIRED
from models.project_stats_model import ProjectStatsModel
from models.task_manager_model import TaskManager
from models.task_model import Task


CRISIS_CRITICAL_BUG = "critical_bug"
CRISIS_BURNOUT = "burnout"
CRISIS_CONFLICT = "conflict"
CRISIS_INFRASTRUCTURE_OUTAGE = "infrastructure_outage"
CRISIS_TECH_DEBT_ISSUE = "tech_debt_issue"

CRISIS_ROLL_INTERVAL = 4.0


@dataclass(frozen=True)
class CrisisEffect:
    budget: int = 0
    morale: int = 0
    quality: int = 0
    tech_debt: int = 0
    client_trust: int = 0
    fatigue: int = 0
    deadline_delta: int = 0
    mood: str | None = None
    remove_last_queued_task: bool = False


@dataclass(frozen=True)
class CrisisOption:
    text: str
    effect: CrisisEffect
    helpful: bool = True


@dataclass(frozen=True)
class CrisisDefinition:
    type_id: str
    title: str
    description: str
    duration: float
    options: tuple[CrisisOption, ...]
    timeout_effect: CrisisEffect


@dataclass
class Crisis:
    id: int
    type_id: str
    employee_name: str
    task_id: int | None
    time_left: float


CRISIS_DEFINITIONS: dict[str, CrisisDefinition] = {
    CRISIS_CRITICAL_BUG: CrisisDefinition(
        CRISIS_CRITICAL_BUG,
        "Критический баг",
        "В задаче всплыл рискованный дефект. Нужен управленческий выбор.",
        25.0,
        (
            CrisisOption(
                "Разобрать причину и исправить с тестом",
                CrisisEffect(budget=-8, quality=6, tech_debt=-3, fatigue=6),
            ),
            CrisisOption(
                "Купить время на тестирование",
                CrisisEffect(budget=-10, client_trust=-4, deadline_delta=12, quality=3),
            ),
            CrisisOption(
                "Быстрый hotfix без тестов",
                CrisisEffect(budget=-2, quality=-5, tech_debt=10, fatigue=8),
                helpful=False,
            ),
            CrisisOption(
                "Сказать, что баг некритичный",
                CrisisEffect(quality=-12, client_trust=-8, tech_debt=6, morale=-4),
                helpful=False,
            ),
        ),
        CrisisEffect(quality=-10, tech_debt=8, morale=-4, fatigue=8),
    ),
    CRISIS_BURNOUT: CrisisDefinition(
        CRISIS_BURNOUT,
        "Выгорание",
        "Сотрудник перегружен и может надолго выпасть из разработки.",
        35.0,
        (
            CrisisOption(
                "Отправить на восстановление",
                CrisisEffect(morale=8, budget=-4, fatigue=-35, mood=MOOD_TIRED),
            ),
            CrisisOption(
                "Снять задачу из очереди",
                CrisisEffect(morale=6, client_trust=-4, fatigue=-18, remove_last_queued_task=True),
            ),
            CrisisOption(
                "Дать премию и выходной",
                CrisisEffect(budget=-14, morale=12, fatigue=-30),
            ),
            CrisisOption(
                "Попросить дожать до релиза",
                CrisisEffect(morale=-12, quality=-4, fatigue=18, mood=MOOD_BURNOUT),
                helpful=False,
            ),
        ),
        CrisisEffect(morale=-12, fatigue=20, mood=MOOD_BURNOUT),
    ),
    CRISIS_CONFLICT: CrisisDefinition(
        CRISIS_CONFLICT,
        "Конфликт",
        "Команда спорит о решении, задача тормозит и портит атмосферу.",
        30.0,
        (
            CrisisOption(
                "Провести короткую фасилитацию",
                CrisisEffect(morale=8, quality=2, budget=-3, fatigue=-4),
            ),
            CrisisOption(
                "Зафиксировать владельца решения",
                CrisisEffect(morale=3, quality=4, fatigue=4),
            ),
            CrisisOption(
                "Перенести спор в письменное решение",
                CrisisEffect(client_trust=-2, morale=4, tech_debt=-2),
            ),
            CrisisOption(
                "Продавить решение сверху",
                CrisisEffect(morale=-10, quality=-3, tech_debt=5, fatigue=8),
                helpful=False,
            ),
        ),
        CrisisEffect(morale=-10, quality=-4, fatigue=8),
    ),
    CRISIS_INFRASTRUCTURE_OUTAGE: CrisisDefinition(
        CRISIS_INFRASTRUCTURE_OUTAGE,
        "Сбой инфраструктуры",
        "Окружение нестабильно, релизная цепочка под угрозой.",
        20.0,
        (
            CrisisOption(
                "Откатить деплой и стабилизировать",
                CrisisEffect(budget=-6, quality=5, client_trust=-3, fatigue=4),
            ),
            CrisisOption(
                "Купить облачные ресурсы",
                CrisisEffect(budget=-16, client_trust=3, quality=2, fatigue=-2),
            ),
            CrisisOption(
                "Поставить временный костыль",
                CrisisEffect(tech_debt=12, quality=-4, budget=-2, fatigue=6),
                helpful=False,
            ),
            CrisisOption(
                "Перезапустить и ждать",
                CrisisEffect(client_trust=-10, quality=-7, morale=-4),
                helpful=False,
            ),
        ),
        CrisisEffect(client_trust=-12, quality=-6, budget=-4),
    ),
    CRISIS_TECH_DEBT_ISSUE: CrisisDefinition(
        CRISIS_TECH_DEBT_ISSUE,
        "Проблема техдолга",
        "Старые быстрые решения мешают текущей задаче.",
        30.0,
        (
            CrisisOption(
                "Выделить мини-рефакторинг",
                CrisisEffect(budget=-8, tech_debt=-14, quality=5, fatigue=6),
            ),
            CrisisOption(
                "Урезать scope задачи",
                CrisisEffect(client_trust=-6, morale=4, tech_debt=-6, deadline_delta=6),
            ),
            CrisisOption(
                "Локальный фикс",
                CrisisEffect(budget=-3, quality=1, tech_debt=5, fatigue=4),
            ),
            CrisisOption(
                "Отложить после релиза",
                CrisisEffect(tech_debt=12, quality=-6, client_trust=-4, fatigue=6),
                helpful=False,
            ),
        ),
        CrisisEffect(tech_debt=10, quality=-6),
    ),
}


STAT_LABELS = {
    "budget": "бюджет",
    "morale": "мораль",
    "quality": "качество",
    "tech_debt": "долг",
    "client_trust": "доверие",
    "fatigue": "усталость",
}

MOOD_LABELS = {
    MOOD_TIRED: "устал",
    MOOD_STRESSED: "стресс",
    MOOD_BURNOUT: "выгорание",
}


def describe_effect(effect: CrisisEffect) -> str:
    parts = []
    for field_name in ("budget", "morale", "quality", "tech_debt", "client_trust", "fatigue"):
        value = getattr(effect, field_name)
        if value == 0:
            continue
        sign = "+" if value > 0 else ""
        parts.append(f"{STAT_LABELS[field_name]} {sign}{value}")

    if effect.deadline_delta:
        sign = "+" if effect.deadline_delta > 0 else ""
        parts.append(f"срок {sign}{effect.deadline_delta}с")

    if effect.mood is not None:
        parts.append(f"настроение: {MOOD_LABELS.get(effect.mood, effect.mood)}")

    if effect.remove_last_queued_task:
        parts.append("последняя задача -> To Do")

    if not parts:
        return "без эффекта"
    return ", ".join(parts)


class CrisisManager:
    def __init__(
        self,
        rng: random.Random | None = None,
        roll_interval: float = CRISIS_ROLL_INTERVAL,
    ) -> None:
        self.rng = rng or random.Random()
        self.roll_interval = roll_interval
        self._roll_timer = 0.0
        self._next_crisis_id = 1
        self.active_crises: dict[int, Crisis] = {}
        self.failed_rolls: dict[str, int] = {}

    def update(
        self,
        dt: float,
        employees: list[EmployeeModel],
        task_manager: TaskManager,
        stats: ProjectStatsModel,
        current_time: float,
    ) -> None:
        self._update_timers(dt, employees, task_manager, stats)
        self._roll_timer += dt
        if self._roll_timer >= self.roll_interval:
            self._roll_timer -= self.roll_interval
            for employee in employees:
                self.roll_for_employee(employee, task_manager, stats, current_time)
        stats.active_crises = len(self.active_crises)

    def roll_for_employee(
        self,
        employee: EmployeeModel,
        task_manager: TaskManager,
        stats: ProjectStatsModel,
        current_time: float,
    ) -> Crisis | None:
        if employee.active_crisis_id is not None or employee.current_task_id is None:
            return None

        task = task_manager.get_task(employee.current_task_id)
        if task is None:
            return None

        base_chance = self.calculate_base_chance(employee, task, task_manager, stats, current_time)
        failed_rolls = self.failed_rolls.get(employee.name, 1)
        chance = min(base_chance * failed_rolls, 0.80)

        if self.rng.random() < chance:
            self.failed_rolls[employee.name] = 1
            crisis_type = self._choose_crisis_type(employee, task, task_manager, stats, current_time)
            return self.create_crisis(crisis_type, employee, task)

        self.failed_rolls[employee.name] = failed_rolls + 1
        return None

    def calculate_base_chance(
        self,
        employee: EmployeeModel,
        task: Task,
        task_manager: TaskManager,
        stats: ProjectStatsModel,
        current_time: float,
    ) -> float:
        load = task_manager.calculate_employee_load(employee, current_time)
        chance = 0.03
        chance += task.difficulty * 0.012
        chance += employee.fatigue * 0.0015
        chance += load * 0.001
        chance += stats.tech_debt * 0.001

        if task.required_skill != employee.role:
            chance += 0.10

        if task.deadline - current_time <= max(10.0, task.estimated_time * 1.2):
            chance += 0.06

        if employee.mood == MOOD_STRESSED:
            chance += 0.08
        elif employee.mood == MOOD_BURNOUT or employee.state == EMPLOYEE_STATE_BURNOUT:
            chance += 0.12

        return max(0.01, min(chance, 0.45))

    def create_crisis(
        self,
        crisis_type: str,
        employee: EmployeeModel,
        task: Task | None = None,
    ) -> Crisis:
        definition = CRISIS_DEFINITIONS[crisis_type]
        crisis = Crisis(
            id=self._next_crisis_id,
            type_id=crisis_type,
            employee_name=employee.name,
            task_id=task.id if task is not None else employee.current_task_id,
            time_left=definition.duration,
        )
        self._next_crisis_id += 1
        self.active_crises[crisis.id] = crisis
        employee.active_crisis_id = crisis.id
        employee.needs_help = True
        return crisis

    def get_crisis(self, crisis_id: int | None) -> Crisis | None:
        if crisis_id is None:
            return None
        return self.active_crises.get(crisis_id)

    def get_definition(self, crisis: Crisis) -> CrisisDefinition:
        return CRISIS_DEFINITIONS[crisis.type_id]

    def resolve_crisis(
        self,
        crisis_id: int,
        option_index: int,
        employees: list[EmployeeModel],
        task_manager: TaskManager,
        stats: ProjectStatsModel,
    ) -> bool:
        crisis = self.active_crises.get(crisis_id)
        if crisis is None:
            return False

        definition = self.get_definition(crisis)
        if not (0 <= option_index < len(definition.options)):
            return False

        employee = self._find_employee(crisis.employee_name, employees)
        if employee is None:
            return False

        option = definition.options[option_index]
        self._apply_effect(option.effect, crisis, employee, task_manager, stats)
        if option.helpful:
            employee.recent_help_timer = 15.0

        self._close_crisis(crisis, employee)
        stats.active_crises = len(self.active_crises)
        return True

    def _update_timers(
        self,
        dt: float,
        employees: list[EmployeeModel],
        task_manager: TaskManager,
        stats: ProjectStatsModel,
    ) -> None:
        expired_ids = []
        for crisis in self.active_crises.values():
            crisis.time_left -= dt
            if crisis.time_left <= 0.0:
                expired_ids.append(crisis.id)

        for crisis_id in expired_ids:
            crisis = self.active_crises.get(crisis_id)
            if crisis is None:
                continue
            employee = self._find_employee(crisis.employee_name, employees)
            if employee is None:
                del self.active_crises[crisis.id]
                continue
            definition = self.get_definition(crisis)
            self._apply_effect(definition.timeout_effect, crisis, employee, task_manager, stats)
            self._close_crisis(crisis, employee)

    def _apply_effect(
        self,
        effect: CrisisEffect,
        crisis: Crisis,
        employee: EmployeeModel,
        task_manager: TaskManager,
        stats: ProjectStatsModel,
    ) -> None:
        stats.apply_changes(
            budget=effect.budget,
            morale=effect.morale,
            quality=effect.quality,
            tech_debt=effect.tech_debt,
            client_trust=effect.client_trust,
        )
        employee.fatigue = max(0.0, min(100.0, employee.fatigue + effect.fatigue))

        if effect.deadline_delta and crisis.task_id is not None:
            task = task_manager.get_task(crisis.task_id)
            if task is not None:
                task.deadline = max(0.0, task.deadline + effect.deadline_delta)

        if effect.remove_last_queued_task:
            task_manager.pop_last_queued_task(employee)

        if effect.mood is not None:
            employee.mood = effect.mood

        if employee.mood == MOOD_BURNOUT or effect.mood == MOOD_BURNOUT:
            employee.state = EMPLOYEE_STATE_BURNOUT
            employee.ready_to_work = False
        elif employee.state == EMPLOYEE_STATE_BURNOUT and employee.fatigue < 95.0:
            employee.state = EMPLOYEE_STATE_IDLE

    def _close_crisis(self, crisis: Crisis, employee: EmployeeModel) -> None:
        self.active_crises.pop(crisis.id, None)
        employee.active_crisis_id = None
        employee.needs_help = False

    def _choose_crisis_type(
        self,
        employee: EmployeeModel,
        task: Task,
        task_manager: TaskManager,
        stats: ProjectStatsModel,
        current_time: float,
    ) -> str:
        load = task_manager.calculate_employee_load(employee, current_time)
        weights = {
            CRISIS_CRITICAL_BUG: 2.0 + task.difficulty,
            CRISIS_BURNOUT: 1.0 + employee.fatigue / 20.0 + max(0.0, load - 70.0) / 10.0,
            CRISIS_CONFLICT: 1.0 + load / 35.0,
            CRISIS_INFRASTRUCTURE_OUTAGE: 4.0 if task.required_skill == "DevOps" else 1.5,
            CRISIS_TECH_DEBT_ISSUE: 1.0 + stats.tech_debt / 18.0,
        }
        if employee.mood == MOOD_BURNOUT or employee.state == EMPLOYEE_STATE_BURNOUT:
            weights[CRISIS_BURNOUT] += 8.0
        if stats.tech_debt >= 60:
            weights[CRISIS_TECH_DEBT_ISSUE] += 5.0

        total = sum(weights.values())
        roll = self.rng.random() * total
        cumulative = 0.0
        for crisis_type, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                return crisis_type
        return CRISIS_CRITICAL_BUG

    def _find_employee(
        self,
        employee_name: str,
        employees: list[EmployeeModel],
    ) -> EmployeeModel | None:
        for employee in employees:
            if employee.name == employee_name:
                return employee
        return None
