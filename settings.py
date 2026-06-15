SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

TILE_SIZE = 40
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

CHARACTER_HITBOX_WIDTH = 32
CHARACTER_HITBOX_HEIGHT = 40
PLAYER_SPRITE_SIZE = 64
PLAYER_WIDTH = CHARACTER_HITBOX_WIDTH
PLAYER_HEIGHT = CHARACTER_HITBOX_HEIGHT
PLAYER_SPEED = 260

WINDOW_TITLE = "PM Simulator"

COLORS = {
    "background": (28, 31, 36),
    "floor": (50, 56, 64),
    "wall": (25, 27, 31),
    "desk": (126, 88, 55),
    "workplace": (75, 92, 108),
    "kitchen": (69, 132, 112),
    "meeting": (82, 92, 145),
    "kanban": (158, 124, 44),
    "grid": (63, 69, 78),
    "player": (235, 238, 245),
    "player_outline": (41, 45, 53),
    "text": (238, 241, 246),
    "muted_text": (176, 184, 194),
    "accent": (97, 174, 239),
}

OFFICE_MAP_LAYOUT = {
    "zones": [
        {"left": 2, "top": 2, "width": 6, "height": 3, "tile": "kanban"},
        {"left": 1, "top": 11, "width": 14, "height": 6, "tile": "kitchen"},
        {"left": 16, "top": 11, "width": 15, "height": 6, "tile": "meeting"},
    ],
    "walls": [
        {"left": 0, "top": 0, "width": GRID_WIDTH, "height": 1},
        {"left": 0, "top": GRID_HEIGHT - 1, "width": GRID_WIDTH, "height": 1},
        {"left": 0, "top": 0, "width": 1, "height": GRID_HEIGHT},
        {"left": GRID_WIDTH - 1, "top": 0, "width": 1, "height": GRID_HEIGHT},
        {"left": 1, "top": 1, "width": GRID_WIDTH - 2, "height": 1},
        {"left": 1, "top": 11, "width": 15, "height": 1},
        {"left": 15, "top": 11, "width": 16, "height": 1},
        {"left": 15, "top": 11, "width": 1, "height": 6},
    ],
    "openings": [
        {"left": 6, "top": 11, "width": 2, "height": 1, "tile": "kitchen"},
        {"left": 15, "top": 13, "width": 1, "height": 2, "tile": "floor"},
        {"left": 23, "top": 11, "width": 2, "height": 1, "tile": "meeting"},
    ],
    "furniture": [
        {"left": 11, "top": 2, "width": 2, "height": 3, "tile": "desk"},
        {"left": 15, "top": 2, "width": 2, "height": 3, "tile": "desk"},
        {"left": 19, "top": 2, "width": 2, "height": 3, "tile": "desk"},
        {"left": 11, "top": 8, "width": 2, "height": 3, "tile": "desk"},
        {"left": 15, "top": 8, "width": 2, "height": 3, "tile": "desk"},
        {"left": 19, "top": 8, "width": 2, "height": 3, "tile": "desk"},
        {"left": 1, "top": 12, "width": 1, "height": 5, "tile": "desk"},
    ],
    "workplaces": [
        {"role": "backend", "left": 10, "top": 3, "width": 1, "height": 1, "tile": "workplace"},
        {"role": "frontend", "left": 14, "top": 3, "width": 1, "height": 1, "tile": "workplace"},
        {"role": "QA", "left": 18, "top": 3, "width": 1, "height": 1, "tile": "workplace"},
        {"role": "DevOps", "left": 10, "top": 9, "width": 1, "height": 1, "tile": "workplace"},
        {"role": "AI", "left": 14, "top": 9, "width": 1, "height": 1, "tile": "workplace"},
    ],
    "labels": [
        ("Рабочая зона", (15, 6)),
        ("Кухня", (8, 14)),
        ("Переговорка", (22, 14)),
        ("Канбан", (4, 3)),
    ],
    "targets": {
        "kanban": (5, 3),
        "kitchen": (7, 13),
        "meeting": (23, 13),
    },
    "wander_targets": [
        (5, 6),
        (9, 8),
        (14, 14),
        (24, 7),
        "kitchen",
        "meeting",
        "kanban",
    ],
}
