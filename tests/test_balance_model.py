import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.scenes.play_controller import PlayController
from models.systems.crisis_model import CrisisManager


class DummyGameController:
    def quit(self) -> None:
        pass


def make_controller() -> PlayController:
    pygame.init()
    return PlayController(DummyGameController())


def assign_idle_matching_employees(controller: PlayController) -> None:
    current_time = controller.task_manager.elapsed_time(controller.project_stats)
    for task in list(controller.task_manager.sorted_available_tasks(current_time)):
        for employee in controller.employees:
            if employee.role == task.required_skill and not employee.is_busy:
                controller.task_manager.assign_task(task.id, employee)
                break


def test_passive_session_no_longer_wins_release() -> None:
    controller = make_controller()

    for _ in range(1805):
        controller.update(0.1)
        if controller.finished:
            break

    assert controller.finished is True
    assert controller.final_result is not None
    assert controller.final_result.won is False
    assert controller.project_stats.tasks_done == 0
    assert controller.project_stats.tasks_failed == 12


def test_good_matching_session_wins_release_with_crisis_handling() -> None:
    controller = make_controller()
    controller.crisis_manager = CrisisManager(random.Random(7))

    for step in range(1805):
        if step % 3 == 0:
            assign_idle_matching_employees(controller)
        for crisis_id in list(controller.crisis_manager.active_crises.keys()):
            controller.crisis_manager.resolve_crisis(
                crisis_id,
                0,
                controller.employees,
                controller.task_manager,
                controller.project_stats,
            )
        controller.update(0.25)
        if controller.finished:
            break

    assert controller.finished is True
    assert controller.final_result is not None
    assert controller.final_result.won is True
    assert controller.project_stats.tasks_done >= 6
