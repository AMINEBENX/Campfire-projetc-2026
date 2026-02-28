"""
WhitePager - Vfx / "Juice" Systems
"""
import pygame
import random
import math
from typing import List, Tuple

from src.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Tuple[int, int, int], lifetime: float, size: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size

    def update(self, dt: float) -> bool:
        """Returns False if particle should die."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        # Scale based on lifetime
        current_size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        pygame.draw.rect(surface, self.color, (int(self.x) + offset_x, int(self.y) + offset_y, current_size, current_size))


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit_explosion(self, x: float, y: float, color: Tuple[int, int, int], count: int = 30):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(0.2, 0.8)
            size = random.uniform(2, 6)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))
            
    def emit_shatter(self, y_level: float, color: Tuple[int, int, int]):
        """Spanws a line of particles across the screen to simulate glass shattering."""
        for _ in range(150):
            x = random.uniform(0, SCREEN_WIDTH)
            y = y_level + random.uniform(-10, 10)
            vx = random.uniform(-50, 50)
            vy = random.uniform(50, 500) # Mostly fall down
            lifetime = random.uniform(0.5, 1.5)
            size = random.uniform(3, 8)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        for p in self.particles:
            p.draw(surface, offset_x, offset_y)


class CameraJuice:
    """Handles screen shake, smooth zoom, and player follow."""
    def __init__(self):
        self.shake_duration = 0.0
        self.shake_intensity = 0.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Smooth follow
        self.follow_x = 0.0
        self.follow_y = 0.0
        
        # Zoom
        self.current_zoom = 1.0
        self.target_zoom = 1.0

    def add_shake(self, intensity: float, duration: float):
        """Overrides current shake if the new one is more intense/longer."""
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)

    def set_follow_target(self, player_x: float, player_y: float):
        """Set the target for the camera to smoothly follow."""
        # Target: center screen on player
        target_x = -(player_x - SCREEN_WIDTH / 2)
        target_y = -(player_y - SCREEN_HEIGHT / 2)
        
        # Smooth lerp with delay
        lerp_speed = 3.0
        self.follow_x += (target_x - self.follow_x) * min(1.0, lerp_speed * 0.016)
        self.follow_y += (target_y - self.follow_y) * min(1.0, lerp_speed * 0.016)

    def set_target_zoom(self, health_ratio: float):
        """
        Zoom in when health is low.
        health_ratio: 0.0 (dead) to 1.0 (full health)
        Maps to zoom: 1.3 (low) to 1.0 (full)
        """
        self.target_zoom = 1.0 + (1.0 - health_ratio) * 0.3
        self.target_zoom = max(1.0, min(1.3, self.target_zoom))

    def update(self, dt: float):
        # Shake
        if self.shake_duration > 0:
            self.shake_duration -= dt
            
            current_intensity = self.shake_intensity * (self.shake_duration / (self.shake_duration + 0.1))
            
            self.offset_x = int(random.uniform(-current_intensity, current_intensity))
            self.offset_y = int(random.uniform(-current_intensity, current_intensity))
        else:
            self.shake_duration = 0
            self.shake_intensity = 0
            self.offset_x = 0
            self.offset_y = 0
            
        # Smooth zoom lerp
        self.current_zoom += (self.target_zoom - self.current_zoom) * min(1.0, 2.0 * dt)

    def get_offset(self) -> Tuple[int, int]:
        return int(self.follow_x) + self.offset_x, int(self.follow_y) + self.offset_y
    
    def get_zoom(self) -> float:
        return self.current_zoom
