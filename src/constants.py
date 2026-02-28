"""
WhitePager - Game Constants
"""
from typing import Tuple

# Screen & Rendering
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60

# Colors (RGB)
BLACK: Tuple[int, int, int] = (0, 0, 0)
WHITE: Tuple[int, int, int] = (255, 255, 255)
SURFACE_COLOR: Tuple[int, int, int] = (255, 100, 100) # Bright for overworld
GHOST_BLUE: Tuple[int, int, int] = (100, 150, 255) # Under-realm color
NEON_GLOW: Tuple[int, int, int] = (200, 50, 255)

# Physics & World State
SURFACE_Y: int = 480          # The Glass Divide coordinate

G_SURFACE: float = 1600.0        # Standard gravity (pixels/sec^2)
G_UNDER: float = 600.0          # Heavy-water gravity
DRAG_SURFACE: float = 0.85    # Standard X velocity decay
DRAG_UNDER: float = 0.90      # High friction/drag in the Under-realm

# Player Constants
PLAYER_SPEED: float = 400.0
JUMP_FORCE: float = -700.0
BURST_UP_FORCE: float = -1200.0 # Force when returning to surface

# Soul State
SOUL_DRAIN_RATE: float = 10.0 # Per second
ECHO_HARVEST_AMOUNT: float = 20.0
MAX_SOUL_ENERGY: float = 100.0
