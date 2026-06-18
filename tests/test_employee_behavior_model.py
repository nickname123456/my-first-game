import random

from models.employee_behavior_model import EmployeeBehaviorSystem
from models.employee_model import (
    EMPLOYEE_STATE_GOING_TO_KANBAN,
    EMPLOYEE_STATE_GOING_TO_WORK,
    EMPLOYEE_STATE_NEEDS_HELP,
    EMPLOYEE_STATE_RESTING,
    EMPLOYEE_STATE_WORKING,
    EmployeeModel,
)
from models.office_map_model import OfficeMapModel
from settings import CHARACTER_HITBOX_HEIGHT, CHARACTER_HITBOX_WIDTH


def make_employee(office_map: OfficeMapModel) -> EmployeeModel:
    work_cell = (10, 4)
    center_x, center_y = office_map.grid_to_center(*work_cell)
    return EmployeeModel(
        "Anton",
        "backend",
        center_x - CHARACTER_HITBOX_WIDTH // 2,
        center_y - CHARACTER_HITBOX_HEIGHT // 2,
        CHARACTER_HITBOX_WIDTH,
        CHARACTER_HITBOX_HEIGHT,
        work_cell=work_cell,
    )


def test_behavior_tree_selects_work_when_task_is_collected() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    employee.current_task_id = 1
    employee.task_picked_up = True
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_WORKING
    assert employee.ready_to_work is True


def test_behavior_tree_selects_kanban_before_work() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    employee.current_task_id = 1
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_GOING_TO_KANBAN
    assert employee.ready_to_work is False
    assert employee.target_cell == office_map.kanban_target


def test_behavior_tree_selects_rest_when_fatigue_is_high() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    employee.current_task_id = 1
    employee.task_picked_up = True
    employee.fatigue = 90.0
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_RESTING
    assert employee.ready_to_work is False
    assert employee.target_cell == office_map.kitchen_target


def test_behavior_tree_sends_employee_with_crisis_to_meeting() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    employee.current_task_id = 1
    employee.task_picked_up = True
    employee.fatigue = 90.0
    employee.needs_help = True
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_NEEDS_HELP
    assert employee.ready_to_work is False
    assert employee.target_cell == office_map.meeting_target


def test_employee_waits_in_meeting_until_help_flag_is_cleared() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    meeting_x, meeting_y = office_map.grid_to_center(*office_map.meeting_target)
    employee.x = meeting_x - employee.width // 2
    employee.y = meeting_y - employee.height // 2
    employee.current_task_id = 1
    employee.task_picked_up = True
    employee.needs_help = True
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_NEEDS_HELP
    assert employee.ready_to_work is False
    assert employee.path == []
    assert employee.target_cell is None

    employee.needs_help = False
    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_GOING_TO_WORK
    assert employee.ready_to_work is False
    assert employee.target_cell == employee.work_cell


def test_employee_animation_tracks_real_path_movement() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    work_cell = employee.work_cell
    assert work_cell is not None
    employee.path = [work_cell, (work_cell[0] - 1, work_cell[1])]
    employee.path_index = 1
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior._move_along_path(employee, office_map, 0.1)

    assert employee.is_moving is True
    assert employee.direction == "left"
    assert employee.animation_time > 0.0


def test_employee_animation_stops_without_path() -> None:
    office_map = OfficeMapModel()
    employee = make_employee(office_map)
    employee.direction = "left"
    employee.is_moving = True
    employee.animation_time = 1.0
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior._move_along_path(employee, office_map, 0.1)

    assert employee.is_moving is False
    assert employee.direction == "left"
    assert employee.animation_time == 0.0
