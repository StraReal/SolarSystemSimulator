import datetime
import math
from math import degrees, radians
import numpy as np
import pygame

central_mass = 1.989e30#kg

central_radius = 695508#km

max_size = 1
zoom_factor = 1
earth_size = 1
kmpx_ratio = np.float64(1)
l2000_max_size = max_size
n_lines = 10
tail_life = 20

gravitational_constant = 6.674e-11#N*m^2/kg^2

fps = 60
dt_scale = 60*24*3 #seconds per frame (with 60fps, having this at 3600 would mean 60 hours per second, or 2 days and a half per second)
dt = dt_scale
frame_count = 0

planets = {
    'Earth': {
        'mass': 5.972e24,
        'radius': 6371,
        'distance': 152028425,
        'angle': 0,
        'velocity': np.array([-4, -29])*25,
        'color': (14, 100, 168)},
    'Jupiter': {
        'mass': 1.898e27,
        'radius': 69911,
        'distance': 778547200,
        'angle': 204.5,
        'velocity': np.array([-4, 29])*10,
        'color': (217,175,118) },
    'Mars': {
        'mass': 6.417e23,
        'radius': 3389.5,
        'distance': 149597870,
        'angle': 282.2,
        'velocity': np.array([-29, -4])*25,
        'color': (193,68,14) },
    'Venus': {
        'mass': 4.867e24,
        'radius': 6051,
        'distance': 2.56e8,
        'angle': 192,
        'velocity': np.array([-4, 29])*25,
        'color': (240,231,231) }

} #mass (kg), radius (km), distance (from the sun) (km), angle (degrees to X+), velocity (km/s)

following = ''
launching = ''
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
clock_font = pygame.font.SysFont("monospace", 20)
clock_rect = pygame.Rect(10, 10, 300, 40)

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

def calculate_distance(x1, y1, x2, y2):
    return np.linalg.norm(np.array([x2 - x1, y2 - y1]))

#central mass position (sun) is always 0,0.
for planet_name, planet in planets.items():
    planet['position'] = calculate_vector(planet['distance'], planet['angle'])
    planet['old_positions'] = []

def compute_frame():
    global velocities, angles, max_size, l2000_max_size, positions, attractions, accelerations, frame_count, camera_x, camera_y, earth_position
    for planet_name, planet in planets.items():
        attraction = calculate_attraction(central_mass, planet['mass'], (calculate_distance(planet['position'][0], planet['position'][1], 0, 0)-central_radius-planet['radius'])*1000)
        planet['acceleration'] = calculate_acceleration(attraction, planet['mass'], planet['position'])
        for other_name, other in planets.items():
            if planet_name != other_name:
                r_vec = np.array(other['position']) - np.array(planet['position'])
                attraction = calculate_attraction(other['mass'], planet['mass'],
                                                  (calculate_distance(planet['position'][0], planet['position'][1],
                                                                     other['position'][0], other['position'][1])-other['radius']-planet['radius'])*1000)
                planet['acceleration'] += calculate_acceleration(attraction, planet['mass'], r_vec)
        planet['velocity'] = calculate_velocity(planet['velocity'], planet['acceleration'], dt)
        planet['angle'] = calculate_angle(planet['velocity'])
        planet['position'] = calculate_position(planet['position'], planet['velocity'], dt)
        if planet_name == 'Earth':
            earth_position = planet['position']
        if frame_count % 2 == 0:
            planet['old_positions'].append(planet['position'])
            if len(planet['old_positions']) >= fps*tail_life:
                planet['old_positions'].pop(0)
    if camera_mode == 2:
        camera_x, camera_y = earth_position
    if frame_count % 2000 == 0 or l2000_max_size > max_size:
        l2000_max_size = max_size
    decrease_factor = 0.999 if l2000_max_size >= max_size else 1
    follow_position = earth_position if not following else planets[following]['position']
    max_size = max(max_size*decrease_factor, abs(follow_position[0]) * 1.1, abs(follow_position[1]) * 1.1)
compute_frame()

print('(Relative to the sun) x:', planets['Earth']['position'][0], ' y:', planets['Earth']['position'][1])
print('Acceleration:', planets['Earth']['acceleration'])
print('Velocity:', planets['Earth']['velocity'])
print('Angle:', planets['Earth']['angle'])

t = datetime.datetime(2026, 6, 21, 0, 0, 0)
print(t)

def screen_to_space(pos):
    x, y = pos
    return kmpx_ratio * (2 * x - 1000) + camera_x, -kmpx_ratio * (2 * y - 1000) + camera_y

def space_to_screen(pos, cam_pos=None):
    if cam_pos is None:
        cam_pos = camera_x, camera_y
    cam_x, cam_y = cam_pos
    x, y = pos
    return ((((x - cam_x) / kmpx_ratio) + 1000) / 2,
    (((y - cam_y) / -kmpx_ratio) + 1000) / 2)

def draw_space():
    global earth_x, earth_y, n_lines, kmpx_ratio, earth_size, old_positions
    surface.fill((0, 0, 0, 0))
    if camera_mode == 0:
        t_zoom_factor = 1
        t_camera_x = 0
        t_camera_y = 0
    else:
        t_zoom_factor = zoom_factor
        t_camera_x = camera_x
        t_camera_y = camera_y

    sun_size = central_radius * 5 / kmpx_ratio
    kmpx_ratio = max_size / screen_size / t_zoom_factor
    visible_area = screen_size * kmpx_ratio
    screen.fill((0, 0, 20))

    lines = (visible_area/(10**math.floor(math.log10(visible_area/2))))
    line_space = screen_size/(visible_area/(10**math.floor(math.log10(visible_area/2))))
    spacezero = space_to_screen((0,0), (t_camera_x, t_camera_y))
    for x in range(round(lines/2) + 1):
        for i in range(2):
            i=1-i*2
            pygame.draw.line(screen, (24, 25, 70), (spacezero[0] + i * line_space * x, 0), (spacezero[0] + i * x * line_space, screen_size), 2)

    for y in range(round(lines / 2) + 1):
        for i in range(2):
            i = 1 - i * 2
            pygame.draw.line(screen, (24, 25, 70), (0, spacezero[1] + i * line_space * y),
                             (screen_size, spacezero[1] + i * line_space * y), 2)

    pygame.draw.line(screen, (255, 255, 255), (spacezero[0], 0), (spacezero[0], screen_size), 2)
    pygame.draw.line(screen, (255, 255, 255), (0, spacezero[1]), (screen_size, spacezero[1]), 2)

    if launching:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        planet_x, planet_y = space_to_screen(planets[launching]['position'], (t_camera_x, t_camera_y))
        ratio = min(math.hypot(mouse_x - planet_x, mouse_y - planet_y) / (screen_size / 2), 1)
        r = int(DEEP_RED[0] * ratio + GREEN[0] * (1 - ratio))
        g = int(DEEP_RED[1] * ratio + GREEN[1] * (1 - ratio))
        b = int(DEEP_RED[2] * ratio + GREEN[2] * (1 - ratio))
        color = (r, g, b)
        pygame.draw.line(screen, color, (mouse_x, mouse_y), (planet_x, planet_y), 5)

    pygame.draw.circle(screen, (200, 100, 10), space_to_screen((0, 0), (t_camera_x, t_camera_y)), sun_size)

    for planet_name, planet in planets.items():
        planet_size = planet['radius'] * 300 / kmpx_ratio
        planet_x, planet_y = space_to_screen(planet['position'], (t_camera_x, t_camera_y))
        pygame.draw.circle(screen, (planet['color']), (planet_x, planet_y), planet_size)

        end_pos = (int(planet_x + planet['velocity'][0] * fps * 180 / kmpx_ratio),
                   int(planet_y + planet['velocity'][1] * fps * 180 / -kmpx_ratio))
        if (0 <= end_pos[0] <= screen_size and 0 <= end_pos[1] <= screen_size) or (
                0 <= planet_x <= screen_size and 0 <= planet_y <= screen_size):
            pygame.draw.line(screen, (200, 200, 200), (planet_x, planet_y), end_pos, 5)

        end_pos = (int(planet_x + planet['acceleration'][0] * fps * 1440 * 2000 / kmpx_ratio),
                   int(planet_y + planet['acceleration'][1] * fps * 1440 * 2000 / -kmpx_ratio))
        if (0 <= end_pos[0] <= screen_size and 0 <= end_pos[1] <= screen_size) or (0 <= planet_x <= screen_size and 0 <= planet_y <= screen_size):
            pygame.draw.line(screen, (200, 0, 0), (planet_x, planet_y), end_pos, 5)
        if planet_name == 'Earth':
            earth_x, earth_y, earth_size = planet_x, planet_y, planet_size
        for i in range(len(planet['old_positions']) - 1):
            pos = space_to_screen(planet['old_positions'][i], (t_camera_x, t_camera_y))
            pos2 = space_to_screen(planet['old_positions'][i + 1], (t_camera_x, t_camera_y))
            alpha = i / len(planet['old_positions']) * 255
            pygame.draw.line(surface, (150, 150, 180, alpha), pos, pos2, 2)
        lpos = space_to_screen(planet['old_positions'][-1], (t_camera_x, t_camera_y))
        pygame.draw.line(screen, (150, 150, 180), lpos, (planet_x, planet_y), 2)
        screen.blit(surface, (0, 0))

    pygame.draw.rect(screen, (100, 100, 150), clock_rect)

    clock_text = str(t.replace(microsecond=0))
    clock_text_surface = clock_font.render(clock_text, True, (255, 255, 255))
    clock_text_rect = clock_text_surface.get_rect(center=clock_rect.center)
    screen.blit(clock_text_surface, clock_text_rect)

def pause(pause=None):
    global paused, dt
    paused = not paused if pause is None else pause
    dt = 0 if paused else dt_scale

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                for planet_name, planet in planets.items():
                    if math.hypot(mouse_x - space_to_screen(planet['position'])[0], mouse_y - space_to_screen(planet['position'])[1]) <= planet['radius'] * 300 / kmpx_ratio:
                        launching = planet_name
                        pause(True)
                if camera_mode == 1 and not launching:
                    orig_space_mouse_x, orig_space_mouse_y = screen_to_space((mouse_x, mouse_y))
                    orig_camera_x, orig_camera_y = camera_x, camera_y
                    moving = True
            elif event.button == 3:
                mouse_x, mouse_y = event.pos
                for planet_name, planet in planets.items():
                    if math.hypot(mouse_x - space_to_screen(planet['position'])[0], mouse_y - space_to_screen(planet['position'])[1]) <= planet['radius'] * 300 / kmpx_ratio:
                        camera_mode = 1
                        camera_x, camera_y = planet['position']
                        following = planet_name
                        print(following)
                    elif following == planet_name:
                        following = None
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if launching:
                    mouse_x, mouse_y = event.pos
                    planets[launching]['velocity'] = np.array([space_to_screen(planets[launching]['position'])[0] - mouse_x, -(space_to_screen(planets[launching]['position'])[1] - mouse_y)]) * math.log10(max_size) ** 1.1
                    launching = ''
                    pause(False)
                    dt=dt_scale
                moving = False
        if event.type == pygame.MOUSEWHEEL:
            if camera_mode == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                zoom_factor = min(100000,max(0.001, zoom_factor * (1 + event.y * 0.1)))
                #camera_x, camera_y = kmpx_ratio * 2 * (mouse_x - 1000) /2+camera_x, kmpx_ratio * 2 * (mouse_y - 1000) /2-camera_y
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                camera_mode = 1 if camera_mode == 0 else 0
            elif event.key == pygame.K_SPACE:
                pause()
                if frame_count % 2 == 0:
                    for planet_name, planet in planets.items():
                        planet['old_positions'].append(planet['position'])
                        if len(planet['old_positions']) >= fps * tail_life:
                            planet['old_positions'].pop(0)
            elif event.key == pygame.K_r:
                dt = 1/60 if dt!=1/60 else dt_scale
    if moving:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        space_mouse_x, space_mouse_y = screen_to_space((mouse_x, mouse_y))
        camera_x, camera_y = orig_camera_x - space_mouse_x+orig_space_mouse_x, orig_camera_y - space_mouse_y+orig_space_mouse_y
        orig_camera_x, orig_camera_y = camera_x, camera_y
        orig_space_mouse_x, orig_space_mouse_y = screen_to_space((mouse_x, mouse_y))
    if not paused:
        compute_frame()
    if following:
        camera_x, camera_y = planets[following]['position']
    draw_space()
    pygame.display.flip()
    clock.tick(fps)
    frame_count += 1
    t += datetime.timedelta(microseconds=round(dt*1000000))