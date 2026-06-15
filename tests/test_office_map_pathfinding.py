from models.office_map_model import OfficeMapModel


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
