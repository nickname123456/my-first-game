from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmployeeModel:
    name: str
    role: str
    x: int
    y: int
    width: int
    height: int

    @property
    def rect(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height
