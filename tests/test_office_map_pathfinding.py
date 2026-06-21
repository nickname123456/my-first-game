from models.world.office_map_model import OfficeMapModel
from models.algorithms.pathfinding_model import astar_path


EXPECTED_WORKPLACES = {
    "backend": (10, 3),
    "frontend": (14, 3),
    "QA": (18, 3),
    "DevOps": (10, 9),
    "AI": (14, 9),
}


def test_neighbors_return_only_walkable_cells() -> None:
    """Проверяем, что метод neighbors возвращает только проходимые клетки и не включает стены и мебель"""
    office_map = OfficeMapModel()

    neighbors = office_map.neighbors((10, 4))

    assert neighbors
    assert all(office_map.is_walkable(*cell) for cell in neighbors)
    assert (11, 4) not in neighbors


def test_find_nearest_walkable_returns_adjacent_floor_for_desk() -> None:
    """Проверяем, что если мы пытаемся встать на клетку с мебелью, то метод find_nearest_walkable возвращает соседнюю проходимую клетку"""
    office_map = OfficeMapModel()

    nearest = office_map.find_nearest_walkable((11, 4))

    assert nearest is not None
    assert office_map.is_walkable(*nearest)


def test_workplaces_are_marked_and_walkable() -> None:
    """Проверяем, что целевые клетки для рабочих мест помечены как WORKPLACE и на них можно встать"""
    office_map = OfficeMapModel()

    assert office_map.workplace_targets == EXPECTED_WORKPLACES
    for cell in EXPECTED_WORKPLACES.values():
        x, y = cell
        assert office_map.grid[y][x] == OfficeMapModel.WORKPLACE
        assert office_map.is_walkable(x, y)


def test_desks_remain_blocked_next_to_workplaces() -> None:
    """Проверяем, что клетки с мебелью, расположенные рядом с рабочими местами, остаются непроходимыми, чтобы сотрудники не могли встать на них"""
    office_map = OfficeMapModel()

    for cell in ((11, 4), (15, 4), (19, 4), (11, 9), (15, 9)):
        x, y = cell
        assert office_map.grid[y][x] == OfficeMapModel.DESK
        assert not office_map.is_walkable(x, y)


def test_astar_can_reach_workplace() -> None:
    """Проверяем, что алгоритм A* может найти путь от канбана до одного из рабочих мест, несмотря на препятствия в виде стен и мебели"""
    office_map = OfficeMapModel()

    path = astar_path(office_map, office_map.kanban_target, office_map.workplace_targets["backend"])

    assert path
    assert path[-1] == office_map.workplace_targets["backend"]
