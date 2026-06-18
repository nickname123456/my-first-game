import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.play_controller import PlayController
from models.crisis_model import CrisisManager
from models.task_model import TASK_STATUS_DONE, TASK_STATUS_FAILED


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


def test_first_three_matching_tasks_finish_before_deadline_without_crises() -> None:
    controller = make_controller()
    controller.crisis_manager = CrisisManager(roll_interval=9999.0, grace_period=9999.0)
    first_three_ids = [task.id for task in controller.task_manager.tasks[:3]]

    for task in list(controller.task_manager.tasks[:3]):
        employee = next(employee for employee in controller.employees if employee.role == task.required_skill)
        controller.task_manager.assign_task(task.id, employee)

    for _ in range(1000):
        controller.update(0.1)
        first_three = [controller.task_manager.get_task(task_id) for task_id in first_three_ids]
        if all(task is not None and task.status in (TASK_STATUS_DONE, TASK_STATUS_FAILED) for task in first_three):
            break

    first_three = [controller.task_manager.get_task(task_id) for task_id in first_three_ids]
    assert all(task is not None and task.status == TASK_STATUS_DONE for task in first_three)
    assert all(task is not None and task.progress == 100.0 for task in first_three)


def test_demo_balance_completes_several_tasks_and_limits_crises() -> None:
    controller = make_controller()
    controller.crisis_manager = CrisisManager(random.Random(7))
    max_active_crises = 0

    for step in range(720):
        if step % 4 == 0:
            assign_idle_matching_employees(controller)
        controller.update(0.25)
        max_active_crises = max(max_active_crises, len(controller.crisis_manager.active_crises))

    assert controller.project_stats.tasks_done >= 4
    assert max_active_crises <= 1
