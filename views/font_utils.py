import pygame


def get_ui_font(size: int) -> pygame.font.Font:
    font = pygame.font.SysFont("arial", size)
    if font is None:
        font = pygame.font.Font(None, size)
    return font
