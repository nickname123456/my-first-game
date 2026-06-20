from __future__ import annotations

import random
from dataclasses import dataclass

from models.entities.employee_model import EMPLOYEE_STATE_BURNOUT, EMPLOYEE_STATE_IDLE, EmployeeModel
from models.systems.task_manager_model import TaskManager


MOOD_NORMAL = "normal"
MOOD_TIRED = "tired"
MOOD_STRESSED = "stressed"
MOOD_BURNOUT = "burnout"

MOODS = (MOOD_NORMAL, MOOD_TIRED, MOOD_STRESSED, MOOD_BURNOUT)
MOOD_UPDATE_INTERVAL = 5.0


@dataclass(frozen=True)
class MoodContext:
    workload: float = 0.0
    deadline_pressure: bool = False
    has_crisis: bool = False
    helped_recently: bool = False
    task_success_recently: bool = False


BASE_TRANSITIONS: dict[str, dict[str, float]] = {
    MOOD_NORMAL: {
        MOOD_NORMAL: 0.82,
        MOOD_TIRED: 0.14,
        MOOD_STRESSED: 0.04,
        MOOD_BURNOUT: 0.00,
    },
    MOOD_TIRED: {
        MOOD_NORMAL: 0.24,
        MOOD_TIRED: 0.62,
        MOOD_STRESSED: 0.13,
        MOOD_BURNOUT: 0.01,
    },
    MOOD_STRESSED: {
        MOOD_NORMAL: 0.12,
        MOOD_TIRED: 0.30,
        MOOD_STRESSED: 0.53,
        MOOD_BURNOUT: 0.05,
    },
    MOOD_BURNOUT: {
        MOOD_NORMAL: 0.00,
        MOOD_TIRED: 0.14,
        MOOD_STRESSED: 0.24,
        MOOD_BURNOUT: 0.62,
    },
}


def normalize_probabilities(probabilities: dict[str, float]) -> dict[str, float]:
    cleaned = {mood: max(0.0, probabilities.get(mood, 0.0)) for mood in MOODS}
    total = sum(cleaned.values())
    if total <= 0.0:
        return {MOOD_NORMAL: 1.0, MOOD_TIRED: 0.0, MOOD_STRESSED: 0.0, MOOD_BURNOUT: 0.0}
    return {mood: value / total for mood, value in cleaned.items()}


class MoodSystem:
    def __init__(
        self,
        rng: random.Random | None = None,
        update_interval: float = MOOD_UPDATE_INTERVAL,
    ) -> None:
        self.rng = rng or random.Random()
        self.update_interval = update_interval
        self._timer = 0.0

    def update(
        self,
        dt: float,
        employees: list[EmployeeModel],
        task_manager: TaskManager,
        current_time: float,
    ) -> None:
        for employee in employees:
            employee.recent_help_timer = max(0.0, employee.recent_help_timer - dt)
            employee.success_boost_timer = max(0.0, employee.success_boost_timer - dt)

        self._timer += dt
        if self._timer < self.update_interval:
            return

        self._timer -= self.update_interval
        for employee in employees:
            context = MoodContext(
                workload=task_manager.calculate_employee_load(employee, current_time),
                deadline_pressure=task_manager.employee_has_deadline_pressure(employee, current_time),
                has_crisis=employee.active_crisis_id is not None,
                helped_recently=employee.recent_help_timer > 0.0,
                task_success_recently=employee.success_boost_timer > 0.0,
            )
            self.update_employee(employee, context)

    def update_employee(self, employee: EmployeeModel, context: MoodContext) -> str:
        probabilities = self.transition_probabilities(employee.mood, context)
        employee.mood = self._weighted_choice(probabilities)

        if employee.mood == MOOD_BURNOUT:
            employee.state = EMPLOYEE_STATE_BURNOUT
            employee.ready_to_work = False
        elif employee.state == EMPLOYEE_STATE_BURNOUT and employee.fatigue < 95.0:
            employee.state = EMPLOYEE_STATE_IDLE

        return employee.mood

    def transition_probabilities(
        self,
        current_mood: str,
        context: MoodContext,
    ) -> dict[str, float]:
        probabilities = dict(BASE_TRANSITIONS.get(current_mood, BASE_TRANSITIONS[MOOD_NORMAL]))
        workload = max(0.0, min(100.0, context.workload))

        if workload >= 60.0:
            probabilities[MOOD_TIRED] += 0.05
            probabilities[MOOD_STRESSED] += 0.08
            probabilities[MOOD_NORMAL] -= 0.06

        if workload >= 85.0:
            probabilities[MOOD_STRESSED] += 0.06
            probabilities[MOOD_BURNOUT] += 0.03
            probabilities[MOOD_NORMAL] -= 0.05

        if context.deadline_pressure:
            probabilities[MOOD_TIRED] += 0.04
            probabilities[MOOD_STRESSED] += 0.05
            probabilities[MOOD_NORMAL] -= 0.04

        if context.has_crisis:
            probabilities[MOOD_STRESSED] += 0.10
            probabilities[MOOD_BURNOUT] += 0.03
            probabilities[MOOD_NORMAL] -= 0.07

        if context.helped_recently:
            probabilities[MOOD_NORMAL] += 0.25
            probabilities[MOOD_TIRED] += 0.05
            probabilities[MOOD_STRESSED] -= 0.16
            probabilities[MOOD_BURNOUT] -= 0.08

        if context.task_success_recently:
            probabilities[MOOD_NORMAL] += 0.14
            probabilities[MOOD_STRESSED] -= 0.06
            probabilities[MOOD_BURNOUT] -= 0.04

        return normalize_probabilities(probabilities)

    def _weighted_choice(self, probabilities: dict[str, float]) -> str:
        roll = self.rng.random()
        cumulative = 0.0
        for mood in MOODS:
            cumulative += probabilities[mood]
            if roll <= cumulative:
                return mood
        return MOOD_NORMAL
