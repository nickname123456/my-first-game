import pygame

from models.notification_model import (
    NOTIFICATION_DANGER,
    NOTIFICATION_INFO,
    NOTIFICATION_WARNING,
    NotificationModel,
)
from settings import COLORS, SCREEN_WIDTH
from views.font_utils import get_ui_font


NOTIFICATION_COLORS = {
    NOTIFICATION_INFO: (47, 68, 78),
    NOTIFICATION_WARNING: (96, 76, 42),
    NOTIFICATION_DANGER: (105, 52, 58),
}


class NotificationView:
    def __init__(self) -> None:
        self.font = get_ui_font(18)

    def draw(self, surface, notifications: list[NotificationModel]) -> None:
        max_visible = 3
        for index, notification in enumerate(notifications[:max_visible]):
            text = self._trim_to_width(notification.text, SCREEN_WIDTH - 48)
            rendered = self.font.render(text, True, COLORS["text"])
            width = min(SCREEN_WIDTH - 32, rendered.get_width() + 24)
            rect = pygame.Rect(16, 48 + index * 36, width, 28)
            fill = NOTIFICATION_COLORS.get(notification.severity, NOTIFICATION_COLORS[NOTIFICATION_INFO])

            pygame.draw.rect(surface, fill, rect, border_radius=4)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1, border_radius=4)
            surface.blit(rendered, (rect.x + 12, rect.y + 5))

    def _trim_to_width(self, text: str, max_width: int) -> str:
        if self.font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        trimmed = text
        while trimmed and self.font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return trimmed + ellipsis
