"""
WhitePager - Player Entity and State Machine
"""
import pygame
import math
from typing import List, Optional

from src.constants import (
    SURFACE_Y, G_SURFACE, G_UNDER, DRAG_SURFACE, DRAG_UNDER,
    PLAYER_SPEED, JUMP_FORCE, BURST_UP_FORCE,
    SOUL_DRAIN_RATE, MAX_SOUL_ENERGY
)
from src.entities.projectiles import Bullet

class Player(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.image = pygame.Surface((50, 70))
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(midbottom=(x, y))
        
        # Physics
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        # State Machine
        self.is_alive = True
        self.health = 100
        self.soul_energy = MAX_SOUL_ENERGY
        
        # Cooldowns and Mechanics
        self.current_fire_rate = 0.2
        self.fire_cooldown = 0.0
        self.dash_cooldown = 0.0
        self.dash_time_left = 0.0
        self.facing_right = True
        
        # Optional Group reference for firing bullets
        self.bullet_group: Optional[pygame.sprite.Group] = None
        
        # Escape portals (list of (x, y, radius))
        self.escape_portals = []  # Will be set by the engine
        self.escaped_through_portal = False

    def toggle_soul_state(self):
        """Triggers the transition into the Under-realm."""
        self.is_alive = False
        self.soul_energy = 50.0  # Start with 50 soul energy
        self.image.fill((150, 200, 255)) # Shift to spectral blue
        self.image.set_alpha(150) # Ghostly transparency
        self.image = pygame.transform.flip(self.image, True, False) # Flip Horizontally
        # Push player slightly down so they pass the line
        self.pos_y = SURFACE_Y + self.rect.height / 2 + 5.0

    def resurrect(self):
        """Triggers the massive geyser return to the Living plane."""
        self.is_alive = True
        self.health = 100
        # Completely reset the image surface to clear spectral alpha artifacts
        self.image = pygame.Surface((50, 70))
        self.image.fill((255, 255, 255))
        # Ensure correct facing direction is maintained
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        self.velocity_y = BURST_UP_FORCE # The massive launch upward

    def shoot(self, target_x: float, target_y: float) -> bool:
        """Instantiates a Bullet towards the target coordinates. Returns True if a bullet was fired."""
        if self.bullet_group is None or self.fire_cooldown > 0:
            return False
            
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        dist = max(math.hypot(dx, dy), 1.0)
        
        speed = 800.0
        v_x = (dx / dist) * speed
        v_y = (dy / dist) * speed
            
        bullet = Bullet(self.rect.centerx, self.rect.centery, v_x, v_y, (255, 200, 0))
        self.bullet_group.add(bullet)
        
        # Determine facing for melee offsets
        self.facing_right = v_x >= 0
        self.fire_cooldown = self.current_fire_rate
        return True

    def dash(self):
        """Perform a rapid dash in the direction the player is currently facing."""
        if self.dash_cooldown > 0:
            return
        
        direction = 1 if self.facing_right else -1
        speed = 2500.0
        self.velocity_x = direction * speed
        self.velocity_y = 0  # Purely horizontal dash
        
        self.dash_time_left = 0.15
        self.dash_cooldown = 1.0

    def melee_attack(self) -> pygame.Rect:
        """Returns a hitbox rect for combat evaluation in the main loop."""
        offset = 40 if self.facing_right else -40
        hitbox = pygame.Rect(0, 0, 50, 50)
        hitbox.center = (self.rect.centerx + offset, self.rect.centery)
        return hitbox

    def take_damage(self, amount: int):
        if not self.is_alive:
            return
        
        self.health -= amount
        # Note: toggle_soul_state is handled by the main engine to coordinate VFX

    def harvest_echo(self, amount: float):
        """Refills soul energy in the Under-realm."""
        if not self.is_alive:
            self.soul_energy += amount
            if self.soul_energy >= MAX_SOUL_ENERGY:
                self.soul_energy = MAX_SOUL_ENERGY
                self.resurrect()

    def _handle_input_alive(self, keys):
        if self.dash_time_left > 0:
            return # Ignore movement inputs while dashing
            
        # Horizontal
        if keys[pygame.K_a]:
            self.velocity_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_d]:
            self.velocity_x = PLAYER_SPEED
            self.facing_right = True

    def _handle_input_soul(self, keys):
        # Under-realm enables omni-directional swimming
        swim_speed = PLAYER_SPEED * 0.8
        if keys[pygame.K_a]:
            self.velocity_x = -swim_speed
            self.facing_right = False
        if keys[pygame.K_d]:
            self.velocity_x = swim_speed
            self.facing_right = True
        if keys[pygame.K_w]:
            self.velocity_y = -swim_speed
        if keys[pygame.K_s]:
            self.velocity_y = swim_speed

    def update(self, dt: float, keys):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.dash_time_left > 0:
            self.dash_time_left -= dt
            
        if self.is_alive:
            self._handle_input_alive(keys)
            
            # Physics - Alive (Overworld)
            self.velocity_x *= DRAG_SURFACE
            self.velocity_y += G_SURFACE * dt
            
            # Predict Position
            next_y = self.pos_y + self.velocity_y * dt
            
            # Solid Surface check
            if next_y + self.rect.height / 2 >= SURFACE_Y:
                self.velocity_y = 0
                self.pos_y = SURFACE_Y - self.rect.height / 2
                
                # Jump handling only when grounded
                if keys[pygame.K_SPACE]:
                    self.velocity_y = JUMP_FORCE
                    # Juice suggestion: spawn jump dust particles
            else:
                self.pos_y = next_y

            self.pos_x += self.velocity_x * dt
            
        else:
            # Physics - Soul (Under-realm, stuck to ceiling/surface line)
            self._handle_input_alive(keys) # Re-use regular movement
            
            # Soul state moves much slower (40% of normal)
            self.velocity_x *= 0.4
            # Invert gravity to fall UP to the surface line
            self.velocity_y -= G_SURFACE * dt
            
            next_y = self.pos_y + self.velocity_y * dt
            
            # Check if player touches a floating portal
            for px, py, pr in self.escape_portals:
                dx = self.pos_x - px
                dy = self.pos_y - py
                if math.hypot(dx, dy) < pr + self.rect.height / 2:
                    self.escaped_through_portal = True
                    break
            
            # Solid ceiling collision (the glass divide line)
            if next_y - self.rect.height / 2 <= SURFACE_Y:
                self.velocity_y = 0
                self.pos_y = SURFACE_Y + self.rect.height / 2
                
                # Jump down
                if keys[pygame.K_SPACE]:
                    self.velocity_y = -JUMP_FORCE # Inverted jump force pushes down
            else:
                self.pos_y = next_y
                
            self.pos_x += self.velocity_x * dt
            
            # No passive drain
            pass
                
        # Update Rect
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        
        # Screen bounds (Y only - X is infinite scroll)
        if self.rect.bottom > 720:
            self.rect.bottom = 720
            self.pos_y = float(self.rect.centery)
        if self.rect.top < 0 and self.is_alive:
            self.rect.top = 0
            self.pos_y = float(self.rect.centery)
        if self.rect.top < SURFACE_Y and not self.is_alive and not self.escaped_through_portal:
            self.rect.top = SURFACE_Y
            self.pos_y = float(self.rect.centery)
            self.velocity_y = max(self.velocity_y, 0) # Bonk head on the glass from below
