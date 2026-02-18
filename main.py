import datetime
import math
from math import degrees, radians
import numpy as np
import pygame

central_mass = 1.989e30#kg
revolving_mass = 5.972e24#kg

central_radius = 695508#km
revolving_radius = 6371#km
relative_radius = central_radius / revolving_radius

distance = 152028425#km
angle = 0#degrees

velocity = np.array([0, 500]) #km/s

max_size = 1
zoom_factor = 1
t_earth_size = 1
kmpx_ratio = np.float64(1)
l2000_max_size = max_size
n_lines = 10
old_positions =[]
tail_life = 20

gravitational_constant = 6.674e-17#N*m^2/kg^2

fps = 60
dt_scale = 60*24*3 #seconds per frame (with 60fps, having this at 3600 would mean 60 hours per second, or 2 days and a half per second)
dt = dt_scale
frame_count = 0

launching = False
moving = False
paused = False

pygame.init()
screen_size = 1000
screen = pygame.display.set_mode((screen_size, screen_size))
surface = pygame.Surface((screen_size, screen_size), pygame.SRCALPHA)

earth_x, earth_y = 0, 0
mouse_x, mouse_y = 0, 0
space_mouse_x, space_mouse_y = 0, 0
orig_space_mouse_x, orig_space_mouse_y = 0, 0
camera_x, camera_y = 0, 0
orig_camera_x, orig_camera_y = 0, 0

camera_mode = 0 #0: heliocentric #1: freecam

GREEN = (0, 255, 0)
DEEP_RED = (139, 0, 0)

def calculate_vector(distance, angle): #2d position (km)
    return np.array([distance * math.cos(radians(angle)), distance * math.sin(radians(angle))])

def calculate_position(s0, v, dt):
    s = s0 + v * dt
    return s

def calculate_attraction(maj_mass, min_mass, distance): #attraction force (Newtons)
    return gravitational_constant * maj_mass * min_mass / distance**2

def calculate_acceleration(F, m, r):
    r_mag = np.linalg.norm(r)
    unit_vect = r / r_mag

    a = -F / m * unit_vect

    return a

def calculate_velocity(v0, a, dt):
    v = v0 + a * dt
    return v

def calculate_angle(v):
    theta = math.atan2(v[1], v[0])

    return degrees(theta)

#central mass position (sun) is always 0,0.
earth_position = calculate_vector(distance, angle)
def compute_frame():
    global velocity, angle, max_size, l2000_max_size, earth_position, attraction, acceleration, frame_count, camera_x, camera_y
    attraction = calculate_attraction(central_mass, revolving_mass, distance)
    acceleration = calculate_acceleration(attraction, revolving_mass, earth_position)
    velocity = calculate_velocity(velocity, acceleration, dt)
    angle = calculate_angle(velocity)
    earth_position = calculate_position(earth_position, velocity, dt)
    old_positions.append(earth_position)
    if len(old_positions) >= fps*tail_life:
        old_positions.pop(0)
    if camera_mode == 2:
        camera_x, camera_y = earth_position
    if frame_count % 2000 == 0 or l2000_max_size > max_size:
        l2000_max_size = max_size
    decrease_factor = 0.999 if l2000_max_size >= max_size else 1
    max_size = max(max_size*decrease_factor, abs(earth_position[0]) * 1.1, abs(earth_position[1]) * 1.1)
compute_frame()

print('(Relative to the sun) x:', earth_position[0], ' y:', earth_position[1])
print('Attraction:', attraction)
print('Acceleration:', acceleration)
print('Velocity:', velocity)
print('Angle:', angle)

t = datetime.datetime(2026, 6, 21, 0, 0, 0)
print(t)

def screen_to_space(pos):
    x, y = pos
    return kmpx_ratio * (2 * x - 1000) + camera_x, kmpx_ratio * (2 * y - 1000) + camera_y

def space_to_screen(pos, cam_pos=None):
    if cam_pos is None:
        cam_pos = camera_x, camera_y
    cam_x, cam_y = cam_pos
    x, y = pos
    return ((((x - cam_x) / kmpx_ratio) + 1000) / 2,
    (((y - cam_y) / kmpx_ratio) + 1000) / 2)

def draw_space():
    global earth_x, earth_y, n_lines, kmpx_ratio, t_earth_size, old_positions
    surface.fill((0, 0, 0, 0))
    if camera_mode == 0:
        t_earth_size = screen_size / 30
        t_sun_size = screen_size / 14
        t_zoom_factor = 1
        t_camera_x = 0
        t_camera_y = 0
    else:
        t_earth_size = math.log10(max(10, revolving_radius / kmpx_ratio * 1000)) * revolving_radius / 10**math.floor(math.log10(revolving_radius))
        t_sun_size = math.log10(max(10, central_radius / kmpx_ratio * 1000)) * central_radius / 10**math.floor(math.log10(central_radius))
        t_zoom_factor = zoom_factor
        t_camera_x = camera_x
        t_camera_y = camera_y
    kmpx_ratio = max_size / screen_size / t_zoom_factor
    visible_area = screen_size * kmpx_ratio
    vis_area_min_x = camera_x - visible_area/2
    vis_area_min_y = camera_y - visible_area/2
    screen.fill((0, 0, 20))

    max_lines = 10
    t_n_lines = max_lines + ((math.log10(visible_area/ t_zoom_factor)**2) % max_lines)
    line_space = screen_to_space((screen_size/t_n_lines, 0))[0] - screen_to_space((0, 0))[0]
    spacezero = space_to_screen((0,0), (t_camera_x, t_camera_y))
    for x in range(round(t_n_lines) + 2):
        pygame.draw.line(screen, (50, 50, 70), (spacezero[0] + screen_size/t_n_lines*(vis_area_min_x//line_space-3) + screen_size/t_n_lines * x, 0), (spacezero[0] + screen_size/t_n_lines*(vis_area_min_x//line_space-3) + screen_size/t_n_lines * x, screen_size), 2)

    for y in range(round(t_n_lines) + 2):
        pygame.draw.line(screen, (50, 50, 70), (0, spacezero[1] + screen_size/t_n_lines*(vis_area_min_y//line_space-3+y)), (screen_size, spacezero[1] + screen_size/t_n_lines*(vis_area_min_y//line_space-3+y)), 2)

    pygame.draw.line(screen, (255, 255, 255), (spacezero[0], 0), (spacezero[0], screen_size), 2)
    pygame.draw.line(screen, (255, 255, 255), (0, spacezero[1]), (screen_size, spacezero[1]), 2)

    if launching:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        ratio = min(math.hypot(mouse_x - earth_x, mouse_y - earth_y) / (screen_size / 2), 1)
        r = int(DEEP_RED[0] * ratio + GREEN[0] * (1 - ratio))
        g = int(DEEP_RED[1] * ratio + GREEN[1] * (1 - ratio))
        b = int(DEEP_RED[2] * ratio + GREEN[2] * (1 - ratio))
        color = (r, g, b)
        pygame.draw.line(screen, color, (mouse_x, mouse_y), (earth_x, earth_y), 5)

    earth_x, earth_y = space_to_screen(earth_position, (t_camera_x, t_camera_y))
    pygame.draw.circle(screen, (200, 100, 10), space_to_screen((0,0), (t_camera_x, t_camera_y)), t_sun_size)
    pygame.draw.circle(screen, (14, 100, 168), (earth_x, earth_y), t_earth_size)

    for i in range(len(old_positions)-1):
        pos = space_to_screen(old_positions[i], (t_camera_x, t_camera_y))
        pos2 = space_to_screen(old_positions[i+1], (t_camera_x, t_camera_y))
        alpha = i/len(old_positions) * 255
        pygame.draw.line(surface, (150,150,180,alpha), pos, pos2, 2)
    screen.blit(surface, (0, 0))

    end_pos = (int(earth_x + velocity[0] * fps * 180 / kmpx_ratio), int(earth_y + velocity[1] * fps * 180 / kmpx_ratio))
    if 0 <= end_pos[0] <= screen_size and 0 <= end_pos[1] <= screen_size:
        pygame.draw.line(screen, (200, 200, 200), (earth_x, earth_y), end_pos, 5)


clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                if math.hypot(mouse_x - earth_x, mouse_y - earth_y) <= t_earth_size:
                    launching = True
                    dt=0
                elif camera_mode == 1:
                    orig_space_mouse_x, orig_space_mouse_y = screen_to_space((mouse_x, mouse_y))
                    orig_camera_x, orig_camera_y = camera_x, camera_y
                    moving = True
            elif event.button == 3:
                mouse_x, mouse_y = event.pos
                if math.hypot(mouse_x - earth_x, mouse_y - earth_y) <= t_earth_size:
                    camera_mode = 2
                    camera_x, camera_y = earth_position
                elif camera_mode == 2:
                    camera_mode = 1
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if launching:
                    mouse_x, mouse_y = event.pos
                    velocity = np.array([earth_x - mouse_x, earth_y - mouse_y]) * math.log10(max_size) ** 1.1
                    print('Velocity:', velocity)
                    launching=False
                    dt=dt_scale
                moving = False
        if event.type == pygame.MOUSEWHEEL:
            if camera_mode == 1 or 2:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                zoom_factor = min(100,max(0.1, zoom_factor + event.y * 0.1 * zoom_factor**1.1))
                #camera_x, camera_y = kmpx_ratio * 2 * (mouse_x - 1000) /2+camera_x, kmpx_ratio * 2 * (mouse_y - 1000) /2-camera_y
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                camera_mode = 1 if camera_mode == 0 else 0
            elif event.key == pygame.K_SPACE:
                paused = not paused
    if moving:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        space_mouse_x, space_mouse_y = screen_to_space((mouse_x, mouse_y))
        camera_x, camera_y = orig_camera_x - space_mouse_x+orig_space_mouse_x, orig_camera_y - space_mouse_y+orig_space_mouse_y
        orig_camera_x, orig_camera_y = camera_x, camera_y
        orig_space_mouse_x, orig_space_mouse_y = screen_to_space((mouse_x, mouse_y))
    if not paused:
        compute_frame()
    draw_space()
    pygame.display.flip()
    clock.tick(fps)
    frame_count += 1