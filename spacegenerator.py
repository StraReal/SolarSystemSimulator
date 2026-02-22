import pygame
import random
from utils import interpolate_colors

def generate_starfield(width, height, star_count=800,
                       min_radius=1, max_radius=3):

    surf = pygame.Surface((width, height)).convert()
    surf.fill((0, 0, 10))

    # ---- stars -------------------------------------------------
    for _ in range(star_count):
        x, y = random.randint(0, width-1), random.randint(0, height-1)
        radius = random.randint(min_radius, max_radius)
        col = (random.randint(200,255), random.randint(200,255), random.randint(200,255))
        col=interpolate_colors(col, (0, 0, 10))

        pygame.draw.circle(surf, col, (x, y), radius)


    return surf
