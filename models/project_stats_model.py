from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectStatsModel:
    release_time_left: int = 180
    budget: int = 100
    morale: int = 100
    quality: int = 100
    tech_debt: int = 0
    client_trust: int = 100
