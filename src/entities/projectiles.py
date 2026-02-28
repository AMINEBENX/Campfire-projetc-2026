"""
WhitePager - Bullet/Projectile Systems
Includes the slow projectile conditional logic.
"""
import pygame
from typing import Tuple

from src.constants import SURFACE_Y, GHOST_BLUE, BLACK, DRAG_UNDER

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, velocity_x: float, velocity_y: float, color: Tuple[int, int, int]):
        super().__init__()
        self.image = pygame.Surface((12, 12)) # make it square since it goes 4 ways
        self.color = color
        self.image.fill(self.color)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        
        # Determine if initially spawned under the surface
        self.in_under_realm = self.pos_y > SURFACE_Y
        self.lifetime = 2.0  # seconds until it despawns

    def update(self, dt: float):
        self.pos_x += self.velocity_x * dt
        self.pos_y += self.velocity_y * dt
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        # Conditional physics: Enter denser medium
        if self.rect.y > SURFACE_Y and not self.in_under_realm:
            self.in_under_realm = True
            self.velocity_x *= 0.4  # Massively slow down the bullet
            self.velocity_y *= 0.4
            self.color = GHOST_BLUE
            self.image.fill(self.color)
            
            
        # Lifetime kill instead of fixed screen coords
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
