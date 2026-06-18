import random

from models.employee_model import EmployeeModel
from models.mood_model import (
    MOOD_NORMAL,
    MOOD_STRESSED,
    MOOD_TIRED,
    MoodContext,
    MoodSystem,
    normalize_probabilities,
)
from settings import CHARACTER_HITBOX_HEIGHT, CHARACTER_HITBOX_WIDTH


def make_employee() -> EmployeeModel:
    return EmployeeModel(
        "Anton",
        "backend",
        0,
        0,
        CHARACTER_HITBOX_WIDTH,
        CHARACTER_HITBOX_HEIGHT,
    )


def test_markov_probabilities_are_normalized() -> None:
    probabilities = normalize_probabilities(
        {
            MOOD_NORMAL: 2.0,
            MOOD_TIRED: 1.0,
            MOOD_STRESSED: -4.0,
        }
    )

    assert round(sum(probabilities.values()), 6) == 1.0
    assert all(value >= 0.0 for value in probabilities.values())


def test_high_workload_raises_stressed_probability() -> None:
    system = MoodSystem(random.Random(1))
    calm = system.transition_probabilities(MOOD_NORMAL, MoodContext(workload=10.0))
    overloaded = system.transition_probabilities(MOOD_NORMAL, MoodContext(workload=95.0))

    assert overloaded[MOOD_STRESSED] > calm[MOOD_STRESSED]


def test_recent_help_raises_normal_probability() -> None:
    system = MoodSystem(random.Random(1))
    stressed = MoodContext(workload=80.0, has_crisis=True)
    helped = MoodContext(workload=80.0, has_crisis=True, helped_recently=True)

    stressed_probabilities = system.transition_probabilities(MOOD_STRESSED, stressed)
    helped_probabilities = system.transition_probabilities(MOOD_STRESSED, helped)

    assert helped_probabilities[MOOD_NORMAL] > stressed_probabilities[MOOD_NORMAL]


def test_mood_update_applies_selected_state() -> None:
    employee = make_employee()
    system = MoodSystem(random.Random(1))

    mood = system.update_employee(employee, MoodContext(workload=95.0, has_crisis=True))

    assert mood in {MOOD_NORMAL, MOOD_TIRED, MOOD_STRESSED, "burnout"}
    assert employee.mood == mood
