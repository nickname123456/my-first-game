import random

from models.employee_behavior_model import EmployeeBehaviorSystem
from models.employee_model import (
    EMPLOYEE_STATE_GOING_TO_KANBAN,
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
    employee.fatigue = 80.0
    behavior = EmployeeBehaviorSystem(random.Random(1))

    behavior.update_employee(0.0, employee, office_map)

    assert employee.state == EMPLOYEE_STATE_RESTING
    assert employee.ready_to_work is False
    assert employee.target_cell == office_map.kitchen_target
