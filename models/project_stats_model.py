from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectStatsModel:
    release_time_left: float = 180.0
    budget: int = 100
    morale: int = 100
    quality: int = 100
    tech_debt: int = 0
    client_trust: int = 100
    tasks_done: int = 0
    tasks_failed: int = 0
    tasks_active: int = 0
