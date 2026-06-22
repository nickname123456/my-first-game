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
    active_crises: int = 0

    # Пример DRY. Другие системы вызывают apply_changes и не повторяют ограничение значений от 0 до 100
    def apply_changes(
        self,
        budget: int = 0,
        morale: int = 0,
        quality: int = 0,
        tech_debt: int = 0,
        client_trust: int = 0,
    ) -> None:
        self.budget = self._clamp_resource(self.budget + budget)
        self.morale = self._clamp_resource(self.morale + morale)
        self.quality = self._clamp_resource(self.quality + quality)
        self.tech_debt = self._clamp_resource(self.tech_debt + tech_debt)
        self.client_trust = self._clamp_resource(self.client_trust + client_trust)

    def clamp_resources(self) -> None:
        self.apply_changes()

    def _clamp_resource(self, value: int) -> int:
        return max(0, min(100, int(value)))
