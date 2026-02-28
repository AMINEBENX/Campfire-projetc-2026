"""
WhitePager - Main Game Engine
Handles initialization, main loop, 60 FPS constraint, and rendering pipeline.
"""
import pygame
import sys
import random
import asyncio

from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BLACK, SURFACE_Y, NEON_GLOW,
    GHOST_BLUE, SURFACE_COLOR, MAX_SOUL_ENERGY
)
from src.entities.player import Player
from src.entities.enemies import BaseEnemy, Echo, PendingEchoes
from src.core.vfx import ParticleSystem, CameraJuice
from src.core.post_processing import PostProcessor
from src.core.audio import AudioManager

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.render_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # Offscreen render target
        pygame.display.set_caption("Souls of the Beneath")
        self.clock = pygame.time.Clock()
        
        # Groups
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.echoes = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        
        # VFX
        self.vfx = ParticleSystem()
        self.camera = CameraJuice()
        self.post_processor = PostProcessor(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Inter-state vars
        self.shattered = False
        self.spawn_timer = 0.0
        self.level = 1
        self.time_survived = 0.0
        self.target_spawn_time = 2.0
        self.dt = 0.016  # Default dt
        self.escape_portals = []  # List of (x, y, radius) for floating portals
        self.echo_spawn_timer = 0.0  # Timer for spawning echoes near portals in underground
        
        # Initial Entities
        self.player = Player(400, SURFACE_Y - 50)
        self.player.bullet_group = self.bullets
        self.all_sprites.add(self.player)
        
        # Spawn some test enemies
        for i in range(3):
            enemy = BaseEnemy(800 + i * 150, SURFACE_Y - 50)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
            
        self.running = True
        self.font = pygame.font.SysFont(None, 36)
        
        # Audio
        self.audio = AudioManager()
        self.audio.start_music()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Single-press actions
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # Combat handling
                if event.key == pygame.K_k: # Melee Attack
                    hitbox = self.player.melee_attack()
                    for enemy in self.enemies:
                        if hitbox.colliderect(enemy.rect):
                            enemy.take_damage(10)
                            self.camera.add_shake(5.0, 0.1) # Hitstop/Shake feel
                            self.vfx.emit_explosion(enemy.rect.centerx, enemy.rect.centery, SURFACE_COLOR, 15)
                
                if event.key == pygame.K_LSHIFT: # Dash
                    self.player.dash()
                    
                if event.key == pygame.K_o: # Damage test
                    self.player.take_damage(100) # instant kill to test shatter
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3: # Right click (Dash)
                    self.player.dash()

    def update(self, dt: float):
        self.dt = dt
        keys = pygame.key.get_pressed()
        
        # Level Scaling (only advance when alive)
        if self.player.is_alive:
            self.time_survived += dt
            new_level = int(self.time_survived / 10) + 1
            if new_level > self.level:
                self.level = new_level
                # Increase difficulty
                self.target_spawn_time = max(0.4, 2.0 - (self.level * 0.15))
                self.player.current_fire_rate = min(0.5, 0.25 + (self.level * 0.025)) # 4/sec at start -> 2/sec at max
            
        # Slow Motion computation based on Health (surface only)
        time_scale = 1.0
        if self.player.is_alive and self.player.health < 25:
            time_scale = 0.3
            
        dt_scaled = dt * time_scale
            
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0] and self.player.is_alive: # Left click Auto-fire (Only overworld)
            mx, my = pygame.mouse.get_pos()
            cx, cy = self.camera.get_offset()
            if self.player.shoot(mx - cx, my - cy):
                self.audio.play_shoot()
        
        # Camera follow & zoom
        self.camera.set_follow_target(self.player.pos_x, self.player.pos_y)
        if self.player.is_alive:
            self.camera.set_target_zoom(self.player.health / 100.0)
            self.audio.update_music_speed(self.player.health, 100.0)
        else:
            self.camera.set_target_zoom(self.player.soul_energy / 100.0)
            self.audio.update_music_speed(self.player.soul_energy, 100.0)
        
        # Update Vfx and Camera
        self.vfx.update(dt_scaled)
        self.camera.update(dt) # Camera runs in real time (screenshake unaffected by slo-mo)
        
        # Update Player
        self.player.update(dt_scaled, keys)
        
        if self.player.is_alive:
            # Player is alive: Handle Overworld logic
            self.enemies.update(dt_scaled)
            self.bullets.update(dt_scaled)
            
            # Check bullet-enemy collisions
            for bullet in self.bullets:
                hit_enemies = pygame.sprite.spritecollide(bullet, self.enemies, False)
                for enemy in hit_enemies:
                    enemy.take_damage(10)
                    bullet.kill()
                    self.vfx.emit_explosion(enemy.rect.centerx, enemy.rect.centery, NEON_GLOW, 10)
                    
            # Check enemy-player collisions
            hit_by_enemies = pygame.sprite.spritecollide(self.player, self.enemies, False)
            for enemy in hit_by_enemies:
                # Add a simple cooldown or knockback to prevent instant death
                # For hackathon simplicity: apply damage and destroy the enemy
                self.player.take_damage(15)
                enemy.die() # Still leaves an echo!
                self.camera.add_shake(10.0, 0.2)
                self.vfx.emit_explosion(self.player.rect.centerx, self.player.rect.centery, SURFACE_COLOR, 20)
                self.audio.play_hurt()
                
            # Enemy Spawning Logic
            self.spawn_timer += dt_scaled
            if self.spawn_timer > self.target_spawn_time:
                self.spawn_timer = 0.0
                # Spawn relative to the PLAYER position for infinite scrolling
                spawn_side = random.choice(["left", "right"])
                if spawn_side == "left":
                    x = self.player.pos_x - SCREEN_WIDTH - 50
                    direction = "right"
                else:
                    x = self.player.pos_x + SCREEN_WIDTH + 50
                    direction = "left"
                new_enemy = BaseEnemy(x, SURFACE_Y - 50, spawn_direction=direction)
                self.enemies.add(new_enemy)
                self.all_sprites.add(new_enemy)
            
            # Check if player health dropped -> SHATTER EVENT
            if self.player.health <= 0 and not self.shattered:
                self.shattered = True
                self.player.toggle_soul_state()
                
                # MASSIVE JUICE
                self.camera.add_shake(20.0, 1.0) # Huge, long screen shake
                self.vfx.emit_shatter(SURFACE_Y, NEON_GLOW) # Glass break particles
                self.audio.play_underground_death()
                
                # Generate a single, rare escape portal far from the player
                self.escape_portals = []
                portal_x = self.player.pos_x + random.choice([-1, 1]) * random.randint(200, 800)
                portal_y = SURFACE_Y + random.randint(50, 200)
                portal_r = random.randint(38, 50)
                self.escape_portals.append((portal_x, portal_y, portal_r))
                self.player.escape_portals = self.escape_portals
                
        else:
            # Player is in Soul State: Handle Under-realm logic
            # Echoes chase player
            for echo in self.echoes:
                echo.update(dt, self.player.pos_x, self.player.pos_y)
            
            self.bullets.update(dt)
            
            # Constantly spawn echoes near escape portals
            self.echo_spawn_timer += dt
            if self.echo_spawn_timer > 2.5 and len(self.echoes) < 8:
                self.echo_spawn_timer = 0.0
                if self.escape_portals:
                    # Pick a random portal to guard
                    px, py, pr = random.choice(self.escape_portals)
                    spawn_x = px + random.randint(-150, 150)
                    echo = Echo(spawn_x, SURFACE_Y + 60, "guard")
                    self.echoes.add(echo)
                    self.all_sprites.add(echo)
            
            # Check bullet-echo collisions for harvesting
            for bullet in self.bullets:
                hit_echoes = pygame.sprite.spritecollide(bullet, self.echoes, False)
                for echo in hit_echoes:
                    echo.take_damage(10)
                    bullet.kill()
                    self.vfx.emit_explosion(echo.rect.centerx, echo.rect.centery, NEON_GLOW, 10)
                    if not echo.alive(): # if it died from this shot
                        self.player.soul_energy += 10.0 
                        self.camera.add_shake(10.0, 0.2)
                        
            # Check Echo-Player collisions (damage)
            hit_by_echoes = pygame.sprite.spritecollide(self.player, self.echoes, False)
            for echo in hit_by_echoes:
                self.player.soul_energy -= 10.0 # Take damage to limit total resurrections
                echo.take_damage(100) # kill echo
                self.camera.add_shake(10.0, 0.2)
                self.vfx.emit_explosion(self.player.rect.centerx, self.player.rect.centery, GHOST_BLUE, 20)
                
            # Resurrection triggering -> Break Surface Event
            # 1. Soul energy hit 100
            soul_maxed = self.player.soul_energy >= MAX_SOUL_ENERGY
            # 2. Player escaped through a portal
            escaped = self.player.escaped_through_portal
            
            if soul_maxed or escaped:
                 self.player.soul_energy = MAX_SOUL_ENERGY
                 self.player.escaped_through_portal = False
                 self.player.escape_portals = []
                 self.escape_portals = []
                 # Kill remaining echoes
                 for echo in self.echoes:
                     echo.kill()
                 self.player.resurrect()
                 self.shattered = False
                 self.camera.add_shake(30.0, 1.5)
                 self.vfx.emit_shatter(SURFACE_Y, SURFACE_COLOR)
                 self.audio.play_revival()
                
            if self.player.soul_energy <= 0 and self.shattered:
                print("Game Over: Soul Extinguished.")
                self.running = False

        # Constantly check for and spawn new Echoes 
        self._spawn_echoes()
        
    def _spawn_echoes(self):
        """Consume the pending list and spawn Echoes."""
        # Wait until there are less than 5 echoes active across the map
        while len(self.echoes) < 5 and len(PendingEchoes) > 0:
            metadata = PendingEchoes.pop(0)
            # Spawn relative to player, spread out
            x_spawn = self.player.pos_x + random.randint(-600, 600)
            echo = Echo(x_spawn, metadata["y_spawn"], metadata["type"])
            self.echoes.add(echo)
            self.all_sprites.add(echo)

    def draw(self):
        self.render_surf.fill(BLACK)
        
        # Calculate camera offset from juice
        cx, cy = self.camera.get_offset()
        
        # 1. Backgrounds - infinite fill based on camera
        if self.player.is_alive:
            # Overworld sky is already black from fill
            # Under-surface dark area extends infinitely
            under_top = SURFACE_Y + cy
            if under_top < SCREEN_HEIGHT:
                surf_rect = pygame.Rect(0, max(0, under_top), SCREEN_WIDTH, SCREEN_HEIGHT)
                pygame.draw.rect(self.render_surf, (10, 15, 30), surf_rect)
            
            # Draw The Glass Divide (infinite line)
            line_y = SURFACE_Y + cy
            if 0 <= line_y <= SCREEN_HEIGHT:
                pygame.draw.line(self.render_surf, NEON_GLOW, (0, line_y), (SCREEN_WIDTH, line_y), 4)
        else:
            # The Under-realm fills the entire screen
            self.render_surf.fill((5, 10, 20))
            # Draw overworld color above the surface line
            line_y = SURFACE_Y + cy
            if line_y > 0:
                over_rect = pygame.Rect(0, 0, SCREEN_WIDTH, min(line_y, SCREEN_HEIGHT))
                pygame.draw.rect(self.render_surf, (15, 10, 25), over_rect)
            
            
            # The Glass Divide (now drawn continuously as a solid line)
            pygame.draw.line(self.render_surf, GHOST_BLUE, (0, line_y), (SCREEN_WIDTH, line_y), 4)
            
            # Draw floating bean-shaped/circular portals in the underground
            for px, py, pr in self.escape_portals:
                screen_px = int(px) + cx
                screen_py = int(py) + cy
                
                # Only draw if roughly on screen
                if -100 <= screen_px <= SCREEN_WIDTH + 100:
                    # Outer Glow Aura (Concentric circles)
                    # We can simulate glow easily by drawing a couple of large transparent-ish circles directly
                    # However Pygame basic shapes don't support alpha directly on the destination surface well without SRCALPHA.
                    # Workaround: just draw a solid darker purple, then wait for Bloom post-processing to do the real glow!
                    glow_w = int(pr * 2.5)
                    glow_h = int(pr * 2.0)
                    glow_rect = pygame.Rect(screen_px - glow_w//2, screen_py - glow_h//2, glow_w, glow_h)
                    pygame.draw.ellipse(self.render_surf, (80, 20, 100), glow_rect)
                    
                    # Inner Portal (Oval/Bean shape)
                    portal_rect = pygame.Rect(screen_px - pr, screen_py - int(pr*0.8), pr * 2, int(pr*1.6))
                    pygame.draw.ellipse(self.render_surf, (30, 10, 50), portal_rect) # Dark purple void
                    pygame.draw.ellipse(self.render_surf, NEON_GLOW, portal_rect, 4) # Neon edge

        # 2. Draw Entities
        for sprite in self.all_sprites:
            self.render_surf.blit(sprite.image, (sprite.rect.x + cx, sprite.rect.y + cy))
            
        for bullet in self.bullets:
            self.render_surf.blit(bullet.image, (bullet.rect.x + cx, bullet.rect.y + cy))
            
        # 3. Draw VFX (Over entities, under UI)
        self.vfx.draw(self.render_surf, offset_x=cx, offset_y=cy)
        
        # Apply Post Processing
        final_screen = self.post_processor.apply_effects(self.render_surf, self.dt)
        
        # Apply Zoom
        zoom = self.camera.get_zoom()
        if zoom > 1.01:
            zw = int(SCREEN_WIDTH / zoom)
            zh = int(SCREEN_HEIGHT / zoom)
            zx = (SCREEN_WIDTH - zw) // 2
            zy = (SCREEN_HEIGHT - zh) // 2
            cropped = final_screen.subsurface((zx, zy, zw, zh))
            self.screen.blit(pygame.transform.scale(cropped, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        else:
            self.screen.blit(final_screen, (0, 0))
        
        # 4. GUI (Static, ignores camera offset)
        if self.player.is_alive:
            hp_text = self.font.render(f"Health: {self.player.health}", True, SURFACE_COLOR)
            self.screen.blit(hp_text, (20, 20))
            
            level_text = self.font.render(f"Level: {self.level}", True, (255, 215, 0))
            self.screen.blit(level_text, (SCREEN_WIDTH - 150, 20))
            # Removed controls text from top of screen as requested
        else:
            soul_text = self.font.render(f"Soul: {int(self.player.soul_energy)}", True, GHOST_BLUE)
            self.screen.blit(soul_text, (20, 20))
            
            level_text = self.font.render(f"Level: {self.level}", True, (50, 200, 150))
            self.screen.blit(level_text, (SCREEN_WIDTH - 150, 20))
            
            # Main underground message
            escape_font = pygame.font.SysFont(None, 48)
            escape_text = escape_font.render("ESCAPE THE BENEATH", True, NEON_GLOW)
            self.screen.blit(escape_text, (SCREEN_WIDTH//2 - escape_text.get_width()//2, 50))
            
            sub_text = self.font.render("Gain back your life! Shoot echoes or find a floating portal!", True, (180, 180, 180))
            self.screen.blit(sub_text, (SCREEN_WIDTH//2 - sub_text.get_width()//2, 90))

        pygame.display.flip()

    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # Delta time in seconds
            self.handle_events()
            self.update(dt)
            self.draw()
            
            # This is required for pygbag / web / asyncio compatibility
            await asyncio.sleep(0)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    engine = GameEngine()
    asyncio.run(engine.run())

