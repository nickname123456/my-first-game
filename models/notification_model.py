from __future__ import annotations

from dataclasses import dataclass


NOTIFICATION_INFO = "info"
NOTIFICATION_WARNING = "warning"
NOTIFICATION_DANGER = "danger"
DEFAULT_NOTIFICATION_TIME = 4.0


@dataclass
class NotificationModel:
    text: str
    time_left: float = DEFAULT_NOTIFICATION_TIME
    severity: str = NOTIFICATION_INFO
