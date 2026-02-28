"""
WhitePager - Asset Cache System
Prioritizing redundant disk I/O reduction via caching.
"""
import pygame
import os
from typing import Dict, Optional

class AssetManager:
    """Manages the caching of Pygame Surface objects to optimize memory/speed."""
    _cache: Dict[str, pygame.Surface] = {}

    @classmethod
    def get_image(cls, filepath: str) -> Optional[pygame.Surface]:
        """
        Loads and returns an image, caching it.
        If the image is already cached, returns the cached surface.
        """
        if filepath in cls._cache:
            return cls._cache[filepath]

        if not os.path.exists(filepath):
            # In a hackathon, returning a placeholder surface is safer than crashing
            print(f"Warning: Missing asset {filepath}, generating placeholder.")
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((255, 0, 255))
            cls._cache[filepath] = placeholder
            return placeholder

        try:
            surface = pygame.image.load(filepath).convert_alpha()
            cls._cache[filepath] = surface
            return surface
        except pygame.error as e:
            print(f"Error loading {filepath}: {e}")
            return None

    @classmethod
    def clear_cache(cls):
        """Releases cached assets."""
        cls._cache.clear()
