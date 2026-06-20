from __future__ import annotations

import heapq
from typing import Protocol # нужно для утиной типизации, чтобы не привязываться к конкретной реализации карты, а просто требовать от нее определенные методы


GridCell = tuple[int, int] # удобно обзывать клетку

# нам все равно какая конкретная реализация карты, главное, чтобы были эти методы, удобно для тестов

# A* не знает про OfficeMapModel
# OfficeMapModel просто удовлетворяет нужному интерфейсу
class PathfindingGrid(Protocol):
    def neighbors(self, cell: GridCell) -> list[GridCell]:
        ...

    def cell_cost(self, cell: GridCell) -> float:
        ...


def manhattan_distance(first: GridCell, second: GridCell) -> int:
    '''
    Эвристика Манхэттена - это метод оценки расстояния между двумя точками на сетке 
    (например, на карте или в головоломках), 
    при котором разрешено перемещаться только по горизонтали и вертикали
    определение с гугла)))
    '''
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def astar_path(grid: PathfindingGrid, start: GridCell, goal: GridCell) -> list[GridCell]:
    # стоим где надо - ниче не делаем
    if start == goal:
        return [start]

    # клетки, которые надо рассмотреть (с приоритетом)
    # внутри - (приоритет, счетчик для разрешения конфликтов при одинаковом приоритете, клетка)
    open_set: list[tuple[float, int, GridCell]] = [] 
    heapq.heappush(open_set, (0.0, 0, start))

    came_from: dict[GridCell, GridCell] = {} # хранит для каждой клетки, откуда мы пришли в эту клетку (для восстановления пути)
    cost_so_far = {start: 0.0} # хранит для каждой клетки, сколько стоит добраться до нее от стартовой клетки
    tie_breaker = 1 # счетчик для разрешения конфликтов при одинаковом приоритете (чем меньше, тем раньше будет рассмотрена клетка)

    while open_set:
        _priority, _order, current = heapq.heappop(open_set) # взять клетку с наименьшим приоритетом (самую перспективную)

        if current == goal: # пришли куда хотели - восстанавливаем путь и возвращаем его
            return _restore_path(came_from, start, goal)

        for next_cell in grid.neighbors(current): # проверка доступных соседей
            new_cost = cost_so_far[current] + grid.cell_cost(next_cell)
            if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]: # нашли лучший путь к соседу
                # это бывает в двух случаях: 
                # 1) мы вообще не были у этого соседа
                # 2) мы нашли более дешевый путь к этому соседу
                # так что обновляем стоимость пути к соседу и добавляем его в очередь на рассмотрение

                cost_so_far[next_cell] = new_cost
                priority = new_cost + manhattan_distance(next_cell, goal)
                heapq.heappush(open_set, (priority, tie_breaker, next_cell))
                tie_breaker += 1
                came_from[next_cell] = current

    return []



def _restore_path(
    came_from: dict[GridCell, GridCell],
    start: GridCell,
    goal: GridCell,
) -> list[GridCell]:
    '''
    восстанавливает путь от цели к старту, 
    используя словарь came_from, 
    и возвращает его в правильном порядке от старта к цели
    '''
    current = goal
    path = [current]

    while current != start:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path
