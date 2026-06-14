import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.play_controller import PlayController
from models.task_model import TASK_STATUS_IN_PROGRESS, TASK_STATUS_TODO


class DummyGameController:
    def __init__(self) -> None:
        self.quit_called = False

    def quit(self) -> None:
        self.quit_called = True


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


def test_mouse_click_on_task_selects_task_without_assignment() -> None:
    controller = make_controller()
    first_task = controller._sorted_tasks()[0]
    controller.view = HitTestView("task", 0)

    controller._handle_kanban_event(mouse_click())

    assert controller.selected_task_id == first_task.id
    assert first_task.status == TASK_STATUS_TODO
    assert all(not employee.is_busy for employee in controller.employees)


def test_mouse_click_on_employee_assigns_selected_task() -> None:
    controller = make_controller()
    task = controller._sorted_tasks()[0]
    controller.selected_task_id = task.id
    controller.view = HitTestView("employee", 0)

    controller._handle_kanban_event(mouse_click())

    assert task.status == TASK_STATUS_IN_PROGRESS
    assert controller.employees[0].is_busy is True
    assert controller.selected_task_id is None


def test_busy_employee_click_does_not_clear_selected_task() -> None:
    controller = make_controller()
    task = controller._sorted_tasks()[0]
    controller.selected_task_id = task.id
    controller.employees[0].current_task_id = 999
    controller.view = HitTestView("employee", 0)

    controller._handle_kanban_event(mouse_click())

    assert task.status == TASK_STATUS_TODO
    assert controller.selected_task_id == task.id
