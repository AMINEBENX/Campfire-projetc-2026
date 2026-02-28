"""
WhitePager - Enemy System and Persistent Echo Mechanics
"""
import pygame
import random
from typing import List, Tuple
from src.constants import SURFACE_Y, G_SURFACE, G_UNDER

# Global persistence list for enemies killed on the Surface
PendingEchoes: List[dict] = []

class BaseEnemy(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, enemy_type: str = "grunt", spawn_direction: str = "left"):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((200, 50, 50))
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.health: int = 20
        self.enemy_type = enemy_type
        
        # Simple AI
        self.velocity_x = -150.0 if spawn_direction == "left" else 150.0
        self.velocity_y = 0.0

    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        # When an enemy dies on the Overworld, persist their soul!
        PendingEchoes.append({
            "type": self.enemy_type,
            "x_spawn": self.rect.centerx,
            "y_spawn": SURFACE_Y + 50 # Spawn just beneath the surface
        })
        self.kill()

    def update(self, dt: float):
        # AI: chance to jump randomly if grounded
        if random.random() < 0.01 * dt * 60:
            if self.pos_y + self.rect.height / 2 >= SURFACE_Y - 5: 
                self.velocity_y = -400.0
                
        # Gravity
        self.velocity_y += G_SURFACE * dt
        self.pos_y += self.velocity_y * dt
        self.pos_x += self.velocity_x * dt
        
        # Surface collision
        if self.pos_y + self.rect.height / 2 >= SURFACE_Y:
            self.pos_y = SURFACE_Y - self.rect.height / 2
            self.velocity_y = 0
            
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        
        # Cleanup if they wander off screen
        if self.rect.right < -200:
            self.kill()


class Echo(pygame.sprite.Sprite):
    """
    The spectral variant of a fallen enemy that flees from the player in the Under-realm.
    """
    def __init__(self, x: float, y: float, enemy_type: str):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((50, 200, 150)) # Spectral greenish
        self.image.set_alpha(150) # Ghostly appearance
        self.rect = self.image.get_rect(center=(x, y))
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.enemy_type = enemy_type
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.chase_speed = 100.0
        self.health = 20
        
    def take_damage(self, amount: int):
        self.health -= amount
        if self.health <= 0:
            self.kill()

    def update(self, dt: float, player_x: float, player_y: float):
        # AI: Chase player on X axis
        if player_x < self.pos_x:
            self.velocity_x = -self.chase_speed
        else:
            self.velocity_x = self.chase_speed
            
        # AI: Teleport closer if player is running away (too far)
        if abs(self.pos_x - player_x) > 1200:
            offset = random.choice([-500, 500])
            self.pos_x = player_x + offset
            
        # AI: Chance to jump from the ceiling (inverted gravity)
        if random.random() < 0.01 * dt * 60:
            if self.pos_y - self.rect.height / 2 <= SURFACE_Y + 5:
                self.velocity_y = 400.0 # Positive jumps down since gravity goes up
            
        # Physics - Walk on Ceiling
        self.velocity_y -= G_SURFACE * dt # Fall UP
        self.pos_y += self.velocity_y * dt
        self.pos_x += self.velocity_x * dt
        
        # Stick to the surface line from below
        if self.pos_y - self.rect.height / 2 <= SURFACE_Y:
            self.pos_y = SURFACE_Y + self.rect.height / 2
            self.velocity_y = 0
            
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
