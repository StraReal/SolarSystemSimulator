import webbrowser
import pygame
import random
import numpy as np

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

def tint_image(image, color):
    rgb_arr = pygame.surfarray.pixels3d(image).astype(np.uint8)
    alpha_arr = pygame.surfarray.pixels_alpha(image).astype(np.uint8)

    tint = np.array(color, dtype=np.uint8)  # (R, G, B)
    gray_norm = rgb_arr[..., 0] / 255.0  # intensity 0‑1 (all channels equal)
    tinted_rgb = (gray_norm[..., None] * tint).astype(np.uint8)

    tmp = pygame.Surface(image.get_size(), pygame.SRCALPHA, 32).convert_alpha()
    # copy tinted RGB
    pygame.surfarray.blit_array(tmp, tinted_rgb)
    # copy the original alpha back onto the temp surface
    pygame.surfarray.pixels_alpha(tmp)[:, :] = alpha_arr
    return tmp


#import numpy as np
#import matplotlib.pyplot as plt
#from vnoise import Noise  # Install via: pip install vnoise
#
#
#def generate_seamless_2d(width, height, scale=0.1):
#    noise = Noise()
#
#    # 1. Create a grid of normalized coordinates (0 to 1)
#    x = np.linspace(0, 1, width, endpoint=False)
#    y = np.linspace(0, 1, height, endpoint=False)
#    X, Y = np.meshgrid(x, y)
#
#    # 2. Map 2D coordinates to circles in 4D space
#    # Radius determines the "variety" of the noise; larger = more detail
#    r = 1.0 / (2 * np.pi)
#
#    # X-axis becomes a circle in dimensions 1 and 2
#    nx = r * np.cos(2 * np.pi * X)
#    ny = r * np.sin(2 * np.pi * X)
#
#    # Y-axis becomes a circle in dimensions 3 and 4
#    nz = r * np.cos(2 * np.pi * Y)
#    nw = r * np.sin(2 * np.pi * Y)
#
#    # 3. Sample the 4D noise at these points
#    # scale controls the "frequency" (zoom level)
#    texture = noise.noise4(nx / scale, ny / scale, nz / scale, nw / scale)
#
#    return texture
#
#
## Generate a 256x256 seamless tile
#tile = generate_seamless_2d(256, 256, scale=0.2)
#
## To prove it tiles, we can concatenate it 2x2
#tiled_view = np.tile(tile, (2, 2))
#
#plt.figure(figsize=(10, 5))
#plt.subplot(1, 2, 1)
#plt.title("Original 256x256 Tile")
#plt.imshow(tile, cmap='gray')
#
#plt.subplot(1, 2, 2)
#plt.title("2x2 Tiled (No Seams!)")
#plt.imshow(tiled_view, cmap='gray')
#plt.show()