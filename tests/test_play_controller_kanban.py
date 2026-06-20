import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.scenes.play_controller import PlayController
from models.entities.task_model import TASK_STATUS_IN_PROGRESS, TASK_STATUS_QUEUED, TASK_STATUS_TODO


class DummyGameController:
    def __init__(self) -> None:
        self.high_score_path = None
        self.result = None

    def quit(self) -> None:
        pass

    def show_result(self, result) -> None:
        self.result = result


class HitTestView:
    def __init__(self, hit_type: str, hit_index: int) -> None:
        self.hit_type = hit_type
        self.hit_index = hit_index

    def hit_test_kanban(self, pos: tuple[int, int]) -> tuple[str, int]:
        return self.hit_type, self.hit_index


def make_controller() -> PlayController:
    pygame.init()
    controller = PlayController(DummyGameController())
    controller.kanban_open = True
    return controller


def mouse_click() -> pygame.event.Event:
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": (0, 0)},
    )


def key_down(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key})


def test_mouse_click_on_employee_assigns_selected_task() -> None:
    controller = make_controller()
    task = controller._sorted_tasks()[0]
    controller.selected_task_id = task.id
    controller.view = HitTestView("employee", 0)

    controller._handle_kanban_event(mouse_click())

    assert task.status == TASK_STATUS_IN_PROGRESS
    assert controller.employees[0].is_busy is True
    assert controller.selected_task_id is None
    assert task.id not in [available_task.id for available_task in controller._sorted_tasks()]


def test_busy_employee_click_queues_selected_task() -> None:
    controller = make_controller()
    task = controller._sorted_tasks()[0]
    controller.selected_task_id = task.id
    controller.employees[0].current_task_id = 999
    controller.view = HitTestView("employee", 0)

    controller._handle_kanban_event(mouse_click())

    assert task.status == TASK_STATUS_QUEUED
    assert task.id in controller.employees[0].task_queue
    assert controller.selected_task_id is None
    assert task.id not in [available_task.id for available_task in controller._sorted_tasks()]


def test_full_employee_click_does_not_clear_selected_task() -> None:
    controller = make_controller()
    task = controller._sorted_tasks()[0]
    controller.selected_task_id = task.id
    controller.employees[0].current_task_id = 999
    controller.employees[0].task_queue = [998, 997]
    controller.view = HitTestView("employee", 0)

    controller._handle_kanban_event(mouse_click())

    assert task.status == TASK_STATUS_TODO
    assert controller.selected_task_id == task.id


def test_blocked_early_release_adds_notification_without_finishing() -> None:
    controller = make_controller()

    controller._handle_kanban_event(key_down(pygame.K_r))

    assert controller.finished is False
    assert controller.final_result is None
    assert controller.notifications
