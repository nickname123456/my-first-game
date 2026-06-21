from __future__ import annotations

import random
from dataclasses import dataclass

from models.algorithms.behavior_tree_model import (
    BT_FAILURE,
    BT_RUNNING,
    BT_SUCCESS,
    ActionNode,
    ConditionNode,
    Selector,
    Sequence,
)
from models.entities.employee_model import (
    EMPLOYEE_STATE_BURNOUT,
    EMPLOYEE_STATE_GOING_TO_KANBAN,
    EMPLOYEE_STATE_GOING_TO_WORK,
    EMPLOYEE_STATE_IDLE,
    EMPLOYEE_STATE_NEEDS_HELP,
    EMPLOYEE_STATE_RESTING,
    EMPLOYEE_STATE_WORKING,
    EmployeeModel,
)
from models.world.office_map_model import OfficeMapModel
from models.algorithms.pathfinding_model import GridCell, astar_path


REST_FATIGUE_THRESHOLD = 85.0 # если усталость выше этого значения, сотрудник будет искать отдых, если ниже - будет продолжать работать
REST_EXIT_THRESHOLD = 45.0 # если усталость ниже этого значения, сотрудник выйдет из состояния отдыха
BURNOUT_FATIGUE_THRESHOLD = 100.0 # если усталость достигает этого значения, сотрудник будет в состоянии выгорания
BASE_WALK_SPEED = 110.0 # базовая скорость ходьбы в пикселях в секунду
WALK_FATIGUE_PER_SECOND = 0.1 # количество усталости, которое сотрудник набирает в секунду при ходьбе
REST_RECOVERY_PER_SECOND = 10.0 # количество усталости, которое сотрудник восстанавливает в секунду во время отдыха


@dataclass
class EmployeeBehaviorContext:
    '''
    объект, который передается в каждый узел Behavior Tree.
    Он содержит все, что нужно для принятия решения:
    - employee - конкретный сотрудник
    - office_map - карта офиса
    - dt - время между кадрами
    '''
    employee: EmployeeModel
    office_map: OfficeMapModel
    dt: float


class EmployeeBehaviorSystem:
    '''
    Отвечает за обновление состояния сотрудников и принятие решений о том, что им делать
    '''
    def __init__(self, rng: random.Random | None = None) -> None:
        '''
        строит дерево:
        Selector
        ├── если needs_help -> идти в переговорку
        ├── если burnout -> ничего не делать
        ├── если устал -> отдыхать
        ├── если есть задача, но не взята у канбана -> идти к канбану
        ├── если задача уже взята -> идти к рабочему месту
        └── иначе гулять
        '''
        self.rng = rng or random.Random()
        self.tree = Selector(
            [
                Sequence(
                    [
                        ConditionNode(self._needs_help),
                        ActionNode(self._go_to_meeting),
                    ]
                ),
                Sequence(
                    [
                        ConditionNode(self._is_burned_out),
                        ActionNode(self._do_nothing),
                    ]
                ),
                Sequence(
                    [
                        ConditionNode(self._needs_rest),
                        ActionNode(self._rest),
                    ]
                ),
                Sequence(
                    [
                        ConditionNode(self._has_task_not_collected),
                        ActionNode(self._go_to_kanban),
                    ]
                ),
                Sequence(
                    [
                        ConditionNode(self._has_collected_task),
                        ActionNode(self._go_to_work),
                    ]
                ),
                ActionNode(self._wander),
            ]
        )

    def update(
        self,
        dt: float,
        employees: list[EmployeeModel],
        office_map: OfficeMapModel,
    ) -> None:
        '''
        обновляет состояние всех сотрудников, вызывая update_employee для каждого из них
        '''
        for employee in employees:
            self.update_employee(dt, employee, office_map)

    def update_employee(
        self,
        dt: float,
        employee: EmployeeModel,
        office_map: OfficeMapModel,
    ) -> str:
        '''
        обновляет состояние конкретного сотрудника, вызывая дерево поведения + двигая его по пути
        '''
        # Если усталость сотрудника достигла порога выгорания, переводим его в состояние выгорания
        if employee.fatigue >= BURNOUT_FATIGUE_THRESHOLD:
            employee.state = EMPLOYEE_STATE_BURNOUT
            employee.mood = "burnout"
            employee.ready_to_work = False

        context = EmployeeBehaviorContext(employee, office_map, dt)
        status = self.tree.tick(context)
        self._move_along_path(employee, office_map, dt)
        return status

    def _is_burned_out(self, context: EmployeeBehaviorContext) -> bool:
        '''проверяет, находится ли сотрудник в состоянии выгорания'''
        return context.employee.state == EMPLOYEE_STATE_BURNOUT or context.employee.mood == "burnout"

    def _needs_help(self, context: EmployeeBehaviorContext) -> bool:
        ''' проверяет, нуждается ли сотрудник в помощи'''
        return context.employee.needs_help

    def _needs_rest(self, context: EmployeeBehaviorContext) -> bool:
        ''' проверяет, нуждается ли сотрудник в отдыхе, с защитой от постоянного переключения'''
        employee = context.employee
        if employee.state == EMPLOYEE_STATE_RESTING:
            return employee.fatigue > REST_EXIT_THRESHOLD
        return employee.fatigue >= REST_FATIGUE_THRESHOLD

    def _has_task_not_collected(self, context: EmployeeBehaviorContext) -> bool:
        ''' проверяет, есть ли у сотрудника задача, но он еще не взял ее у канбана'''
        employee = context.employee
        return employee.current_task_id is not None and not employee.task_picked_up

    def _has_collected_task(self, context: EmployeeBehaviorContext) -> bool:
        ''' проверяет, есть ли у сотрудника задача, и он уже взял ее у канбана'''
        employee = context.employee
        return employee.current_task_id is not None and employee.task_picked_up

    def _do_nothing(self, context: EmployeeBehaviorContext) -> str:
        ''' ничего не делает, если сотрудник в состоянии выгорания'''
        employee = context.employee
        employee.ready_to_work = False
        employee.path = []
        employee.target_cell = None
        return BT_RUNNING

    def _go_to_meeting(self, context: EmployeeBehaviorContext) -> str:
        ''' отправляет сотрудника в переговорку, если он нуждается в помощи'''
        employee = context.employee
        employee.state = EMPLOYEE_STATE_NEEDS_HELP
        employee.ready_to_work = False
        self._set_destination(employee, context.office_map, context.office_map.meeting_target)
        if self._is_at_cell(employee, context.office_map.meeting_target, context.office_map):
            employee.path = []
            employee.target_cell = None
        return BT_RUNNING

    def _rest(self, context: EmployeeBehaviorContext) -> str:
        ''' отправляет сотрудника отдыхать, если он устал'''
        employee = context.employee
        employee.ready_to_work = False
        self._set_destination(employee, context.office_map, context.office_map.kitchen_target)

        if self._is_at_cell(employee, context.office_map.kitchen_target, context.office_map):
            # Если сотрудник находится в кухне, он отдыхает и восстанавливает усталость
            employee.state = EMPLOYEE_STATE_RESTING
            employee.fatigue = max(
                0.0,
                employee.fatigue - REST_RECOVERY_PER_SECOND * context.dt,
            )
            if employee.fatigue <= REST_EXIT_THRESHOLD:
                # Если усталость сотрудника снизилась ниже порога выхода из отдыха, он возвращается в состояние ожидания
                employee.state = EMPLOYEE_STATE_IDLE
                employee.path = []
                employee.target_cell = None
                return BT_SUCCESS
            return BT_RUNNING

        employee.state = EMPLOYEE_STATE_RESTING
        return BT_RUNNING

    def _go_to_kanban(self, context: EmployeeBehaviorContext) -> str:
        ''' отправляет сотрудника к канбану, если у него есть задача, но он еще не взял ее'''
        employee = context.employee
        employee.state = EMPLOYEE_STATE_GOING_TO_KANBAN
        employee.ready_to_work = False
        self._set_destination(employee, context.office_map, context.office_map.kanban_target)

        if self._is_at_cell(employee, context.office_map.kanban_target, context.office_map):
            employee.task_picked_up = True
            employee.path = []
            employee.target_cell = None
            return BT_SUCCESS

        return BT_RUNNING

    def _go_to_work(self, context: EmployeeBehaviorContext) -> str:
        ''' отправляет сотрудника к его рабочему месту, если у него есть задача и он уже взял ее'''
        employee = context.employee
        if employee.work_cell is None:
            return BT_FAILURE

        self._set_destination(employee, context.office_map, employee.work_cell)

        if self._is_at_cell(employee, employee.work_cell, context.office_map):
            employee.state = EMPLOYEE_STATE_WORKING
            employee.ready_to_work = True
            employee.path = []
            employee.target_cell = None
            return BT_SUCCESS

        employee.state = EMPLOYEE_STATE_GOING_TO_WORK
        employee.ready_to_work = False
        return BT_RUNNING

    def _wander(self, context: EmployeeBehaviorContext) -> str:
        ''' отправляет сотрудника гулять, если у него нет задачи и он не устал'''
        employee = context.employee
        employee.ready_to_work = False

        if employee.target_cell is None or not employee.path or self._path_finished(employee):
            target = self.rng.choice(context.office_map.wander_targets)
            self._set_destination(employee, context.office_map, target)

        employee.state = EMPLOYEE_STATE_IDLE
        return BT_RUNNING

    def _set_destination(
        self,
        employee: EmployeeModel,
        office_map: OfficeMapModel,
        target_cell: GridCell,
    ) -> None:
        ''' устанавливает путь сотрудника к целевой клетке, используя алгоритм A* для поиска пути'''
        # Если целевая клетка недоступна, ищем ближайшую доступную клетку
        target_cell = office_map.find_nearest_walkable(target_cell) or target_cell

        if employee.target_cell == target_cell and employee.path:
            # Если сотрудник уже идет к этой клетке и путь не пустой, ничего не делаем
            return

        start = self._employee_cell(employee, office_map) # определяем текущую клетку сотрудника
        start = office_map.find_nearest_walkable(start) or start # если текущая клетка недоступна, ищем ближайшую доступную клетку
        path = astar_path(office_map, start, target_cell)

        employee.target_cell = target_cell
        employee.path = path
        employee.path_index = 1 if len(path) > 1 else 0

    def _move_along_path(
        self,
        employee: EmployeeModel,
        office_map: OfficeMapModel,
        dt: float,
    ) -> None:
        ''' двигает сотрудника по его пути, если он есть'''
        if not employee.path or self._path_finished(employee):
            employee.set_movement_state(None, False, dt)
            return

        target_cell = employee.path[employee.path_index]
        target_center_x, target_center_y = office_map.grid_to_center(*target_cell)
        target_x = target_center_x - employee.width // 2
        target_y = target_center_y - employee.height // 2
        dx = target_x - employee.x
        dy = target_y - employee.y
        distance = (dx * dx + dy * dy) ** 0.5

        if distance == 0:
            employee.path_index += 1
            employee.set_movement_state(None, False, dt)
            return

        previous_x = employee.x
        previous_y = employee.y
        speed = self._walk_speed(employee)
        step = speed * dt
        if step >= distance:
            employee.x = target_x
            employee.y = target_y
            employee.path_index += 1
        else:
            employee.x += round(dx / distance * step)
            employee.y += round(dy / distance * step)

        movement_dx = employee.x - previous_x
        movement_dy = employee.y - previous_y
        direction = self._direction_from_movement(movement_dx, movement_dy)
        employee.set_movement_state(direction, movement_dx != 0 or movement_dy != 0, dt)

        if employee.state != EMPLOYEE_STATE_RESTING:
            employee.fatigue = min(
                BURNOUT_FATIGUE_THRESHOLD,
                employee.fatigue + WALK_FATIGUE_PER_SECOND * dt,
            )

    def _path_finished(self, employee: EmployeeModel) -> bool:
        return employee.path is not None and employee.path_index >= len(employee.path)

    def _is_at_cell(
        self,
        employee: EmployeeModel,
        cell: GridCell,
        office_map: OfficeMapModel,
    ) -> bool:
        return self._employee_cell(employee, office_map) == cell

    def _employee_cell(
        self,
        employee: EmployeeModel,
        office_map: OfficeMapModel,
    ) -> GridCell:
        center_x = employee.x + employee.width / 2
        center_y = employee.y + employee.height / 2
        return office_map.world_to_grid(center_x, center_y)

    def _walk_speed(self, employee: EmployeeModel) -> float:
        fatigue_multiplier = max(0.45, 1.0 - employee.fatigue / 160.0)
        return BASE_WALK_SPEED * fatigue_multiplier

    def _direction_from_movement(self, dx: int, dy: int) -> str | None:
        if dx == 0 and dy == 0:
            return None
        if abs(dx) >= abs(dy):
            if dx < 0:
                return "left"
            return "right"
        if dy < 0:
            return "up"
        return "down"
