import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.play_controller import PlayController
from models.crisis_model import CRISIS_DEFINITIONS
from models.crisis_model import CrisisManager
from models.notification_model import NotificationModel
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


def test_wrong_assignments_and_bad_crisis_choices_lose_release() -> None:
    controller = make_controller()
    controller.crisis_manager = CrisisManager(random.Random(3))

    for step in range(1805):
        if step % 3 == 0:
            current_time = controller.task_manager.elapsed_time(controller.project_stats)
            for task in list(controller.task_manager.sorted_available_tasks(current_time)):
                for employee in controller.employees:
                    if employee.role != task.required_skill and controller.task_manager.employee_has_capacity(employee):
                        controller.task_manager.assign_task(task.id, employee)
                        break

        for crisis_id, crisis in list(controller.crisis_manager.active_crises.items()):
            option_index = len(CRISIS_DEFINITIONS[crisis.type_id].options) - 1
            controller.crisis_manager.resolve_crisis(
                crisis_id,
                option_index,
                controller.employees,
                controller.task_manager,
                controller.project_stats,
            )

        controller.update(0.1)
        if controller.finished:
            break

    assert controller.finished is True
    assert controller.final_result is not None
    assert controller.final_result.won is False


def test_play_controller_collects_overdue_task_notification() -> None:
    controller = make_controller()
    controller.project_stats.release_time_left = 178.0
    controller.task_manager.tasks[0].deadline = 1.0

    controller.update(0.1)

    assert any("Просрочена задача" in notification.text for notification in controller.notifications)


def test_play_controller_expires_notifications_after_timer() -> None:
    controller = make_controller()
    controller.notifications = [NotificationModel("test", time_left=0.1)]

    controller._update_notifications(0.2)

    assert controller.notifications == []
