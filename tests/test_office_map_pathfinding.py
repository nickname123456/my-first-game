from models.office_map_model import OfficeMapModel
from models.pathfinding_model import astar_path


EXPECTED_WORKPLACES = {
    "backend": (10, 3),
    "frontend": (14, 3),
    "QA": (18, 3),
    "DevOps": (10, 9),
    "AI": (14, 9),
}


def test_neighbors_return_only_walkable_cells() -> None:
    office_map = OfficeMapModel()

    neighbors = office_map.neighbors((10, 4))

    assert neighbors
    assert all(office_map.is_walkable(*cell) for cell in neighbors)
    assert (11, 4) not in neighbors


def test_find_nearest_walkable_returns_adjacent_floor_for_desk() -> None:
    office_map = OfficeMapModel()

    nearest = office_map.find_nearest_walkable((11, 4))

    assert nearest is not None
    assert office_map.is_walkable(*nearest)


def test_workplaces_are_marked_and_walkable() -> None:
    office_map = OfficeMapModel()

    assert office_map.workplace_targets == EXPECTED_WORKPLACES
    for cell in EXPECTED_WORKPLACES.values():
        x, y = cell
        assert office_map.grid[y][x] == OfficeMapModel.WORKPLACE
        assert office_map.is_walkable(x, y)


def test_desks_remain_blocked_next_to_workplaces() -> None:
    office_map = OfficeMapModel()

    for cell in ((11, 4), (15, 4), (19, 4), (11, 9), (15, 9)):
        x, y = cell
        assert office_map.grid[y][x] == OfficeMapModel.DESK
        assert not office_map.is_walkable(x, y)


def test_astar_can_reach_workplace() -> None:
    office_map = OfficeMapModel()

    path = astar_path(office_map, office_map.kanban_target, office_map.workplace_targets["backend"])

    assert path
    assert path[-1] == office_map.workplace_targets["backend"]
