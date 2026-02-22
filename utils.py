import webbrowser
import pygame
import random

def interpolate_colors(col1, col2):
    col3 = ((col1[0]+col2[0])/2, (col1[1]+col2[1])/2, (col1[2]+col2[2])/2,)
    return col3
def open_url(target_url): #ONLY USED TO OPEN GITHUB REPO LINK
    """Launch the default browser to target_url."""
    webbrowser.open_new(target_url)

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

def cprint(text, color="w") -> None:
    """
    :param text: text to print
    :param color: color to print in (red, green, yellow, blue, magenta, cyan, white)
    :return: None
    """
    colors = {
        "r": "\033[91m",
        "g": "\033[92m",
        "y": "\033[93m",
        "b": "\033[94m",
        "m": "\033[95m",
        "c": "\033[96m",
        "w": "\033[97m",
    }
    RESET = "\033[0m"
    print(f"{colors.get(color, colors['w'])}{text}{RESET}")

def solar_radius_to_km(value, reverse=False):
    return value / 696,342 if reverse else value*696,342

def solar_mass_to_km(value, reverse=False):
    return value / 1.988475e30 if reverse else value*1.988475e30