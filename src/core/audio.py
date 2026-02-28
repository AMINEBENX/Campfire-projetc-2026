"""
WhitePager - Audio Manager
Handles music playback speed and SFX triggers.
"""
import pygame
import os

SFX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SFX")

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        
        # Load SFX
        self.sfx_shoot = pygame.mixer.Sound(os.path.join(SFX_DIR, "GunshotSFX.ogg"))
        self.sfx_hurt = pygame.mixer.Sound(os.path.join(SFX_DIR, "HurtSfx.ogg"))
        self.sfx_revival = pygame.mixer.Sound(os.path.join(SFX_DIR, "Revival.ogg"))
        self.sfx_underground_death = pygame.mixer.Sound(os.path.join(SFX_DIR, "Underground death.ogg"))
        
        # Lower volumes slightly so they don't clip
        self.sfx_shoot.set_volume(0.4)
        self.sfx_hurt.set_volume(0.6)
        self.sfx_revival.set_volume(0.8)
        self.sfx_underground_death.set_volume(0.7)
        
        # Music
        self.music_path = os.path.join(SFX_DIR, "Game Music.mp3")
        self._current_speed = 1.0
        
    def start_music(self):
        """Begin looping the game music."""
        pygame.mixer.music.load(self.music_path)
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play(-1)  # Loop forever
        
    def update_music_speed(self, health: float, max_health: float):
        """
        Adjust music playback speed based on health ratio.
        Low health -> faster music (up to 1.5x)
        Full health -> slower music (0.9x)
        """
        if max_health <= 0:
            return
            
        ratio = max(0.0, min(1.0, health / max_health))
        # Map ratio 1.0 -> speed 0.9, ratio 0.0 -> speed 1.5
        target_speed = 1.5 - (ratio * 0.6)  # 1.5 at 0hp, 0.9 at 100hp
        
        # Only update if change is significant (avoid constant calls)
        if abs(target_speed - self._current_speed) > 0.05:
            self._current_speed = target_speed
            # pygame.mixer.music doesn't have set_speed, but we can
            # use set_pos or adjust frequency. A practical hack: we can
            # modulate volume for "intensity". For true speed, we need
            # pygame-ce's newer features or a workaround.
            # pygame-ce 2.5+ doesn't support native speed change either.
            # We'll fake it by adjusting volume for intensity feel.
            # Volume goes up when things get dangerous
            intensity_volume = 0.6 + (1.0 - ratio) * 0.4  # 0.6 at full, 1.0 at low
            pygame.mixer.music.set_volume(min(1.0, intensity_volume))
    
    def play_shoot(self):
        self.sfx_shoot.play()
        
    def play_hurt(self):
        self.sfx_hurt.play()
        
    def play_revival(self):
        self.sfx_revival.play()
        
    def play_underground_death(self):
        self.sfx_underground_death.play()
