"""
WhitePager - Post Processing Pipeline
CRT scanlines (scrolling), Bloom, Chromatic Aberration, Vignette.
"""
import pygame

class PostProcessor:
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        
        # Internal surfaces for effects
        self.bloom_surf = pygame.Surface((w // 4, h // 4))
        self.vignette_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Scrolling CRT scanlines
        # Make scanline texture 2x height so we can scroll it
        self.scanline_h = h * 2
        self.scanline_surf = pygame.Surface((w, self.scanline_h), pygame.SRCALPHA)
        self.scanline_offset = 0.0
        
        self._generate_scanlines()
        self._generate_vignette()
        
    def _generate_scanlines(self):
        """Pre-render CRT scanlines onto a tall transparent surface for scrolling."""
        for y in range(0, self.scanline_h, 4):
            pygame.draw.line(self.scanline_surf, (0, 0, 0, 70), (0, y), (self.w, y), 2)
            
    def _generate_vignette(self):
        """Pre-render a dark radial gradient for the corners."""
        center_x, center_y = self.w // 2, self.h // 2
        max_dist = (center_x**2 + center_y**2)**0.5
        
        for radius in range(int(max_dist), 0, -20):
            alpha = int(min(255, 255 * (radius / max_dist)**2))
            pygame.draw.circle(self.vignette_surf, (0, 0, 0, alpha), (center_x, center_y), radius, 20)

    def apply_effects(self, screen: pygame.Surface, dt: float) -> pygame.Surface:
        """Applies Chromatic Aberration, Bloom, scrolling CRT, and Vignette."""
        final_surf = screen.copy()
        
        # 1. Chromatic Aberration
        aberration_offset = 3
        
        r_shift = pygame.Surface((self.w, self.h))
        r_shift.blit(screen, (aberration_offset, 0))
        r_shift.fill((255, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
        
        b_shift = pygame.Surface((self.w, self.h))
        b_shift.blit(screen, (-aberration_offset, 0))
        b_shift.fill((100, 100, 255), special_flags=pygame.BLEND_RGB_MULT)
        
        final_surf.fill((180, 200, 180), special_flags=pygame.BLEND_RGB_MULT)
        final_surf.blit(r_shift, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        final_surf.blit(b_shift, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        # 2. Bloom
        pygame.transform.scale(screen, (self.w // 4, self.h // 4), self.bloom_surf)
        self.bloom_surf.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_SUB)
        bloom_upscaled = pygame.transform.scale(self.bloom_surf, (self.w, self.h))
        final_surf.blit(bloom_upscaled, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        # 3. Scrolling CRT Scanlines
        self.scanline_offset += dt * 60.0  # scroll speed in px/sec
        if self.scanline_offset >= self.h:
            self.scanline_offset -= self.h
            
        y_off = int(self.scanline_offset)
        # Blit the tall scanline texture shifted upward by the offset
        final_surf.blit(self.scanline_surf, (0, -y_off))
        
        # 4. Vignette
        final_surf.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        return final_surf
