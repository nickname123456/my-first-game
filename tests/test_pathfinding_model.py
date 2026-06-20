from models.algorithms.pathfinding_model import astar_path


class SimpleGrid:
    def __init__(self, width: int, height: int, blocked: set[tuple[int, int]]) -> None:
        self.width = width
        self.height = height
        self.blocked = blocked

    def neighbors(self, cell: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = cell
        result = []
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            next_cell = (x + dx, y + dy)
            next_x, next_y = next_cell
            if (
                0 <= next_x < self.width
                and 0 <= next_y < self.height
                and next_cell not in self.blocked
            ):
                result.append(next_cell)
        return result

    def cell_cost(self, cell: tuple[int, int]) -> float:
        return 1.0


def test_astar_finds_path_around_obstacle() -> None:
    grid = SimpleGrid(5, 5, {(2, 0), (2, 1), (2, 2), (2, 3)})

    path = astar_path(grid, (0, 0), (4, 0))

    assert path[0] == (0, 0)
    assert path[-1] == (4, 0)
    assert all(cell not in grid.blocked for cell in path)
    assert (2, 4) in path


def test_astar_returns_empty_path_when_goal_is_unreachable() -> None:
    grid = SimpleGrid(3, 3, {(1, 0), (1, 1), (1, 2)})

    assert astar_path(grid, (0, 1), (2, 1)) == []
