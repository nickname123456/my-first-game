import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from controllers.play_controller import PlayController
from models.task_model import (
    TASK_STATUS_DONE,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_QUEUED,
    TASK_STATUS_TODO,
)
from settings import SCREEN_HEIGHT, SCREEN_WIDTH


class DummyGameController:
    def __init__(self) -> None:
        self.quit_called = False
        self.high_score_path = None
        self.result = None

    def quit(self) -> None:
        self.quit_called = True

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


def finish_full_task_pool(controller: PlayController) -> None:
    while controller.task_manager.spawn_task(current_time=0.0) is not None:
        pass
    for task in controller.task_manager.tasks:
        task.status = TASK_STATUS_DONE
        task.progress = 100.0
    controller.project_stats.release_time_left = 90.0
    controller.task_manager.sync_stats(controller.project_stats)


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
    assert task.id not in [available_task.id for available_task in controller._sorted_tasks()]


def test_tutorial_advances_after_first_assignment() -> None:
    controller = make_controller()
    controller.kanban_open = False

    assert controller.tutorial_opened_kanban is False
    assert controller._gameplay_hint() is not None

    controller._open_kanban()
    assert controller.tutorial_opened_kanban is True
    assert controller.tutorial_selected_task is False

    sorted_tasks = controller._sorted_tasks()
    controller._select_task_by_index(sorted_tasks)
    assert controller.tutorial_selected_task is True

    controller._assign_selected_task()
    assert controller.tutorial_assigned_task is True
    assert controller.tutorial_crisis_hint_timer > 0.0


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


def test_draw_open_kanban_passes_task_counters_to_view() -> None:
    controller = make_controller()
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    controller.draw(surface)


def test_r_key_in_open_kanban_finishes_early_release() -> None:
    controller = make_controller()
    finish_full_task_pool(controller)

    controller._handle_kanban_event(key_down(pygame.K_r))

    assert controller.finished is True
    assert controller.final_result is not None
    assert controller.final_result.won is True
    assert controller.final_result.early_release is True
    assert controller.final_result.score > controller.final_result.base_score


def test_early_release_button_finishes_game() -> None:
    controller = make_controller()
    finish_full_task_pool(controller)
    controller.view = HitTestView("early_release", -1)

    controller._handle_kanban_event(mouse_click())

    assert controller.finished is True
    assert controller.final_result is not None
    assert controller.final_result.early_release is True


def test_blocked_early_release_adds_notification_without_finishing() -> None:
    controller = make_controller()

    controller._handle_kanban_event(key_down(pygame.K_r))

    assert controller.finished is False
    assert controller.final_result is None
    assert any("Досрочный релиз недоступен" in item.text for item in controller.notifications)
