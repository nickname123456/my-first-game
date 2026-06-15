from pathlib import Path

import pygame

from models.player_model import PlayerModel
from settings import COLORS, PLAYER_SPRITE_SIZE


class PlayerView:
    FRAME_COLUMNS = 3
    FRAME_ROWS = 4
    FRAME_WIDTH = 64
    FRAME_HEIGHT = 64
    DRAW_SIZE = PLAYER_SPRITE_SIZE
    WALK_FPS = 8
    IDLE_FRAME = 1
    SPRITESHEET_PATH = (
        Path(__file__).resolve().parent.parent / "assets" / "sprites" / "pm" / "walk.png"
    )
    DIRECTION_ROWS = {
        "down": 0,
        "left": 1,
        "right": 2,
        "up": 3,
    }

    def __init__(self) -> None:
        self.frames = self._load_frames()

    def draw(self, surface, model: PlayerModel) -> None:
        if self.frames is None:
            self._draw_fallback(surface, model)
            return

        direction_frames = self.frames.get(model.direction)
        if direction_frames is None:
            direction_frames = self.frames["down"]

        if model.is_moving:
            frame_index = int(model.animation_time * self.WALK_FPS) % self.FRAME_COLUMNS
        else:
            frame_index = self.IDLE_FRAME

        image = direction_frames[frame_index]
        hitbox = pygame.Rect(*model.rect)
        draw_rect = self._sprite_rect_for_hitbox(hitbox)
        surface.blit(image, draw_rect)

    def _load_frames(self) -> dict[str, list[pygame.Surface]] | None:
        try:
            spritesheet = pygame.image.load(str(self.SPRITESHEET_PATH)).convert_alpha()
        except (FileNotFoundError, pygame.error):
            return None

        frames: dict[str, list[pygame.Surface]] = {}
        for direction, row in self.DIRECTION_ROWS.items():
            frames[direction] = []
            for column in range(self.FRAME_COLUMNS):
                frame_rect = pygame.Rect(
                    column * self.FRAME_WIDTH,
                    row * self.FRAME_HEIGHT,
                    self.FRAME_WIDTH,
                    self.FRAME_HEIGHT,
                )
                frame = spritesheet.subsurface(frame_rect).copy()
                scaled_frame = pygame.transform.scale(
                    frame,
                    (self.DRAW_SIZE, self.DRAW_SIZE),
                )
                frames[direction].append(scaled_frame)

        return frames

    def _draw_fallback(self, surface, model: PlayerModel) -> None:
        hitbox = pygame.Rect(*model.rect)
        visual = self._sprite_rect_for_hitbox(hitbox)
        pygame.draw.rect(surface, COLORS["player"], visual)
        pygame.draw.rect(surface, COLORS["player_outline"], visual, 2)

    def _sprite_rect_for_hitbox(self, hitbox: pygame.Rect) -> pygame.Rect:
        rect = pygame.Rect(0, 0, self.DRAW_SIZE, self.DRAW_SIZE)
        rect.midbottom = hitbox.midbottom
        return rect
