import pygame

from settings import COLORS, PLAYER_HEIGHT, PLAYER_SPEED, PLAYER_WIDTH


class Player:
    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.interact_requested = False

    def handle_input(self, keys, dt: float) -> None:
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.rect.x += round(direction.x * PLAYER_SPEED * dt)
        self.rect.y += round(direction.y * PLAYER_SPEED * dt)
        self.interact_requested = bool(keys[pygame.K_e])

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        pygame.draw.rect(surface, COLORS["player"], self.rect)
        pygame.draw.rect(surface, COLORS["player_outline"], self.rect, 2)
