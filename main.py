import datetime
import math
from math import degrees, radians
import numpy as np
import pygame
import re
from collections import deque
import time

central_mass = 1.989e30#kg

central_radius = 695508#km

max_size = 1
zoom_factor = 1
earth_size = 1
kmpx_ratio = np.float64(1)
l2000_max_size = max_size
n_lines = 10
tail_life = 20
min_trail_dist = 3500000

gravitational_constant = 6.674e-11#N*m^2/kg^2

SCI_NOTATION_RE = re.compile(
    r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$'
)

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
        'color': (240,231,231) },
    'Saturn': {
        'mass': 5.683e26,
        'radius': 58232,
        'distance': 1.44e9,
        'angle': 317.4,
        'velocity': np.array([29, 29]) * 5,
        'color': (205, 133, 63),
        'has_rings': True}

} #mass (kg), radius (km), distance (from the sun) (km), angle (degrees to X+), velocity (km/s)

following = ''
launching = ''
moving = False
paused = False
real_sizes = False
real_time = False
creating = False
writing = False
settings_on = False

pygame.init()
pygame.key.set_repeat(300, 30)
screen_size = 1000
bar_size = 300
total_size = screen_size+bar_size
screen = pygame.display.set_mode((total_size, screen_size))
surface = pygame.Surface((total_size, screen_size), pygame.SRCALPHA)

sidebar = pygame.Rect(screen_size, 0, bar_size, screen_size)

name_rect = pygame.Rect(screen_size+20, 10, bar_size-40, 40)
mass_rect = pygame.Rect(screen_size+20, 70, bar_size-40, 40)
radius_rect = pygame.Rect(screen_size+20, 120, bar_size-40, 40)
velocity_rect = pygame.Rect(screen_size+20, 170, bar_size-40, 40)
velocity_rect_y = pygame.Rect(screen_size+20, 170+15, bar_size-40, 40)

delete_rect = pygame.Rect(screen_size+ bar_size/2+8, screen_size-40-10, bar_size/2 - 16, 40)
deleteimage = pygame.image.load('assets/DeleteIcon.png').convert_alpha()
deleteimage = pygame.transform.smoothscale(deleteimage, (delete_rect.width,
                                             delete_rect.height))

edit_rect = pygame.Rect(screen_size+12, screen_size-40-10, bar_size/2 - 16, 40)
editimage = pygame.image.load('assets/EditIcon.png').convert_alpha()
editimage = pygame.transform.smoothscale(editimage, (edit_rect.width,
                                             edit_rect.height))

create_rect = pygame.Rect(total_size/2-400, 200, 800, 600)
create_text_rect = pygame.Rect(create_rect.left, create_rect.top+10, create_rect.width, 40)
confirm_rect = pygame.Rect(create_rect.left+create_rect.width/4, create_rect.top+create_rect.height-50, create_rect.width/2, 40)
color_rect = pygame.Rect(create_rect.left+3*create_rect.width/4+10, create_rect.top+create_rect.height-50, create_rect.width/4-20, 40)

earth_x, earth_y = 0, 0
mouse_x, mouse_y = 0, 0
space_mouse_x, space_mouse_y = 0, 0
orig_space_mouse_x, orig_space_mouse_y = 0, 0
camera_x, camera_y = 0, 0
orig_camera_x, orig_camera_y = 0, 0
creating_x, creating_y = 0, 0

camera_mode = 0 #0: heliocentric #1: freecam

GREEN = (0, 255, 0)
DEEP_RED = (139, 0, 0)
clock_font = pygame.font.SysFont("monospace", 20)
title_font = pygame.font.SysFont("monospace", 30)
clock_rect = pygame.Rect(10, 10, 300, 40)
pos_rect = pygame.Rect(screen_size-300-10, 10, 300, 40)

class InputBox:
    def __init__(self, name, y, h, value='', input_type: type =bool, anim_time=0.3, acceptszero=False):
        self.name = name
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active   = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.acceptszero = acceptszero
        self.input_type = input_type

        w, _ = clock_font.size(self.name)
        self.trect = pygame.Rect(create_rect.left + 0.66,
                                 create_rect.top + 60 + y,
                                 w + 20,
                                 h)


        if value is not None:
            self.value = value
        else:
            try:
                self.value = self.input_type()
            except Exception as exc:
                raise TypeError(
                    f"The type {self.input_type!r} cannot be instantiated without arguments; "
                    "provide an explicit defaultvalue."
                ) from exc

        self.txt_input = self.input_type in (int, float, str)
        if self.txt_input:
            self.value = str(self.value)
            left=max(w + 20, int(create_rect.width * 0.11))
            self.orig_rect = pygame.Rect(create_rect.left + left, create_rect.top + 60 + y, create_rect.width-left-20, h)
            self.rect = self.orig_rect.copy()
            self.txt_surface = clock_font.render(str(value), True, pygame.Color('white'))
            self.active = False
            pygame.scrap.init()
            pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

        elif self.input_type is bool:
            self.settinglength = 98

            self.srect = pygame.Rect(create_rect.left + 0.66 + w + 20, create_rect.top + 60 + y, self.settinglength, h)

            self._anim_time = anim_time  # seconds for a full toggle
            self._anim_dir = 0
            self.frames_per_toggle = int(fps * self._anim_time)
            self._frames_elapsed = 0


            self._frames = [
                pygame.transform.scale(pygame.image.load(f'assets/Switch_{i + 1}-5.png').convert_alpha(), (self.srect.width,
                                                         self.srect.height))
                for i in range(5)
            ]

            if self.value:
                self.switch = self._frames[4]
                self._frames_elapsed = 18
            else:
                self.switch=self._frames[0]

            self._update_values()

    def _isvalid(self):
        """Return True if `self.raw_text` can be cast to `self.input_type`."""
        try:
            self.input_type(self.value)
            return True
        except Exception:
            return False

    def _clean_text(self, txt: str) -> str:
        """Remove null characters and other unwanted control codes."""
        # keep only printable characters (including spaces)
        return ''.join(ch for ch in txt if ch.isprintable() and not ch.isspace())

    def _activate(self, activate=True):
        global writing
        self.active = activate
        self.color = self.color_active if self.active else self.color_inactive
        writing = writing or self.active

    def toggle(self):
        self.value = not self.value

        self._anim_dir = 1 if self.value else -1
        if self._frames_elapsed < 0:
            self._frames_elapsed = 0
            self._anim_dir = 0
        elif self._frames_elapsed > self.frames_per_toggle:
            self._frames_elapsed = self.frames_per_toggle
            self._anim_dir = 0

        self._update_image()

    def _smoothstep(self, x):
        return 3 * x * x - 2 * x**3

    def _update_image(self):
        p = self._frames_elapsed / self.frames_per_toggle if self.frames_per_toggle else 1.0
        p = max(0.0, min(1.0, p))  # clamp
        p = self._smoothstep(p)

        frame_idx = int(round(p * (len(self._frames) - 1)))
        self.switch = self._frames[frame_idx]

    def _update_values(self, event=None):
        if event is None:
            pos = -1, -1
        else:
            pos = event.pos
        if self.txt_input:
            self._activate(self.rect.collidepoint(pos))
            if not self.active:
                entered = self.value
                if self._isvalid():
                    entered = self.input_type(entered)
                    self._activate(False)
                    return entered
                return None
        elif self.input_type is bool:
            if self.srect.collidepoint(pos):
                self.toggle()
                return self.value
            return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._update_values(event)
        if event.type == pygame.KEYDOWN:
            if self.txt_input and self.active:
                if event.key == pygame.K_RETURN:
                    entered = self.value
                    if self._isvalid():
                        entered = self.input_type(entered)
                        self._activate(False)
                        return entered
                    return None
                elif event.key == pygame.K_BACKSPACE:
                    self.value = self.value[:-1]
                else:
                    self.value += self._clean_text(event.unicode)
                self.txt_surface = clock_font.render(self.value, True, pygame.Color('white'))
                ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

                if ctrl and event.key == pygame.K_v:  # Paste
                    try:
                        clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clip:
                            paste_text = clip.decode('utf-8')
                            self.value += self._clean_text(paste_text)
                            self.txt_surface = clock_font.render(self.value, True, pygame.Color('white'))
                    except Exception:
                        pass
                    return None

    def update(self):
        if self.txt_input:
            width = max(self.orig_rect.w, self.txt_surface.get_width() + 10)
            self.rect.w = width
        elif self.input_type is bool:
            if self._anim_dir == 0:
                return

            self._frames_elapsed += self._anim_dir
            if self._frames_elapsed <= 0:
                self._frames_elapsed = 0
                self._anim_dir = 0
            elif self._frames_elapsed >= self.frames_per_toggle:
                self._frames_elapsed = self.frames_per_toggle
                self._anim_dir = 0
            self._update_image()

    def draw(self, surface):
        text = self.name
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.trect.center)
        screen.blit(text_surface, text_rect)

        if self.txt_input:
            surface.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
            pygame.draw.rect(surface, self.color, self.rect, 2)
        elif self.input_type is bool:
            switch_rect = self.switch.get_rect(topleft=self.srect.topleft)
            screen.blit(self.switch, switch_rect)


inputs = {'Name': {'type':str, 'h':40, 'value':'Planet_Name'},
          'Mass': {'type':float, 'h':40, 'value':'5.972e24'},
          'Radius': {'type':float, 'h':40, 'value':'6371'},
          'R': {"type":int, 'h':40, 'value':14,'acceptszero':True,}, 'G':{'type':int, 'h':40, 'value':100,'acceptszero':True,}, 'B':{'type':int, 'h':40, 'value':168,'acceptszero':True,},
          'Has Rings': {'type':bool, 'h':42, 'value':False}}

input_boxes=[]
results=[]
y=0
for name, vars in inputs.items():
    results.append(None)
    if not 'h' in vars:
        vars['h'] = 40
    if not 'acceptszero' in vars:
        vars['acceptszero'] = False
    print(vars)
    input_boxes.append(InputBox(name, y, vars['h'], vars['value'], vars['type'], acceptszero=vars['acceptszero']))
    y+=vars['h'] + 20

#TODO merge Setting class with InputBox class
class Setting:
    def __init__(self, name, y, h=40, value=None, type=bool, anim_time = 0.3):
        self.type = type
        self.name = name
        if value is not None:
            self.value = value
        else:
            try:
                self.value = self.type()
            except Exception as exc:
                raise TypeError(
                    f"The type {self.type!r} cannot be instantiated without arguments; "
                    "provide an explicit defaultvalue."
                ) from exc
        w, _ = clock_font.size(self.name)
        self.trect = pygame.Rect(create_rect.left + 0.66,
                                 create_rect.top + 60 + y,
                                 w + 20,
                                 h)

        if type==bool:
            self.settinglength = 98

            self.srect = pygame.Rect(create_rect.left + 0.66 + w + 20, create_rect.top + 60 + y, self.settinglength, h)

            self._anim_time = anim_time  # seconds for a full toggle
            self._anim_dir = 0
            self.frames_per_toggle = int(fps * self._anim_time)
            self._frames_elapsed = 0


            self._frames = [
                pygame.transform.scale(pygame.image.load(f'assets/Switch_{i + 1}-5.png').convert_alpha(), (self.srect.width,
                                                         self.srect.height))
                for i in range(5)
            ]

            if self.value:
                self.switch = self._frames[4]
                self._frames_elapsed = 18
            else:
                self.switch=self._frames[0]

    def __repr__(self):
        return self.name + '=' + str(self.value)

    def toggle(self):
        self.value = not self.value

        self._anim_dir = 1 if self.value else -1
        if self._frames_elapsed < 0:
            self._frames_elapsed = 0
            self._anim_dir = 0
        elif self._frames_elapsed > self.frames_per_toggle:
            self._frames_elapsed = self.frames_per_toggle
            self._anim_dir = 0

        self._update_image()
    def _smoothstep(self, x):
        return 3 * x * x - 2 * x**3

    def _update_image(self):
        p = self._frames_elapsed / self.frames_per_toggle if self.frames_per_toggle else 1.0
        p = max(0.0, min(1.0, p))  # clamp
        p = self._smoothstep(p)

        frame_idx = int(round(p * (len(self._frames) - 1)))
        self.switch = self._frames[frame_idx]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.type is bool:
                if self.srect.collidepoint(event.pos):
                    self.toggle()
                    return self.value
        return None

    def update(self):
        if self._anim_dir == 0:
            return

        self._frames_elapsed += self._anim_dir
        if self._frames_elapsed <= 0:
            self._frames_elapsed = 0
            self._anim_dir = 0
        elif self._frames_elapsed >= self.frames_per_toggle:
            self._frames_elapsed = self.frames_per_toggle
            self._anim_dir = 0

        self._update_image()

    def draw(self):
        text = self.name
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.trect.center)
        screen.blit(text_surface, text_rect)

        if self.type is bool:
            switch_rect = self.switch.get_rect(topleft=self.srect.topleft)
            screen.blit(self.switch, switch_rect)

settings = [[True, 'Transparent Trails', 42, bool],]
setting_objs = []
y=0
for setting in settings:
    setting_objs.append(Setting(setting[1], y, h=setting[2], value=setting[0], type=setting[3]))
    y += setting[2]

def create_planet(name, mass, radius, color, x, y, has_rings=False):
    global planets, creating
    planets[name] = {
        'mass': mass,
        'radius': radius,
        'color': color,
        'position': np.array([x, y]),
        'old_positions': deque(maxlen=fps*tail_life),
        'velocity': np.array([0, 0]),
        'has_rings': has_rings,
    }
    creating=False

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
    planet['old_positions'] = deque(maxlen=fps*tail_life)
    if 'has_rings' not in planet:
        planet['has_rings'] = False

def maybe_append(trail, new_pos):
    if not trail:
        trail.append(new_pos)
        return

    last = trail[-1]
    dx, dy = new_pos[0] - last[0], new_pos[1] - last[1]
    if math.hypot(dx, dy) >= min_trail_dist:
        trail.append(new_pos)

def compute_frame(count_frame=False):
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
                planet['acceleration'] += calculate_acceleration(attraction, planet['mass'], -r_vec)
        planet['velocity'] = calculate_velocity(planet['velocity'], planet['acceleration'], dt)
        planet['angle'] = calculate_angle(planet['velocity'])
        planet['position'] = calculate_position(planet['position'], planet['velocity'], dt)
        if planet_name == 'Earth':
            earth_position = planet['position']
        count_frame = count_frame or frame_count % 2 == 0
        if count_frame:
            maybe_append(planet['old_positions'], planet['position'])
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

def calculate_planet_size(radius, is_sun=False): #returns radius from radius
    multiplier = (25 if is_sun else 300) if not real_sizes else 1
    return radius / kmpx_ratio * multiplier

def is_color_valid(col):
    try:
        #print(col)
        pygame.Color(col)
        return True
    except Exception:
        return False

def is_scientific_number(txt: str) -> bool:
    """Return True if *txt* is a valid float written in scientific notation
    (plain decimal numbers are also accepted)."""
    # Empty string is allowed while the user is still typing
    if txt == '':
        return True
    return bool(SCI_NOTATION_RE.fullmatch(txt))

def draw_space():
    global earth_x, earth_y, n_lines, kmpx_ratio, earth_size, old_positions,writing
    surface.fill((0, 0, 0, 0))

    if camera_mode == 0:
        t_zoom_factor = 1
        t_camera_x = 0
        t_camera_y = 0
    else:
        t_zoom_factor = zoom_factor
        t_camera_x = camera_x
        t_camera_y = camera_y

    kmpx_ratio = max_size / screen_size / t_zoom_factor
    sun_size = calculate_planet_size(central_radius, is_sun=True)
    visible_area = screen_size * kmpx_ratio
    va_min_x = t_camera_x - visible_area/2
    va_min_y = (-t_camera_y) - visible_area/2
    screen.fill((0, 0, 20))

    lines = (visible_area/(10**math.floor(math.log10(visible_area/2))))
    line_space = screen_size/lines
    spacemin = space_to_screen((va_min_x, va_min_y), (t_camera_x, t_camera_y))
    spacezero = space_to_screen((0,0), (t_camera_x, t_camera_y))
    neglines = (math.floor((spacezero[0]-spacemin[0])/line_space), math.floor((spacezero[1]-spacemin[1])/line_space))
    for x in range(round(lines/2) + 5):
        for i in range(2):
            i=1-i*2
            pygame.draw.line(screen, (24, 25, 70), (spacezero[0] + i * line_space * (x-neglines[0]*i), 0), (spacezero[0] + i * (x-neglines[0]*i) * line_space, screen_size), 2)

    for y in range(round(lines / 2) + 5):
        for i in range(2):
            i = 1 - i * 2
            pygame.draw.line(screen, (24, 25, 70), (0, spacezero[1] + i * line_space * -(y - neglines[1] * i)),
                             (screen_size, spacezero[1] + i * line_space * -(y - neglines[1] * i)), 2)

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

    pygame.draw.circle(screen, (200, 100, 10), spacezero, sun_size)

    for planet_name, planet in planets.items():
        planet_size = calculate_planet_size(planet['radius'])
        if following == planet_name:
            planet_x, planet_y = 500, 500
        else:
            planet_x, planet_y = space_to_screen(planet['position'], (t_camera_x, t_camera_y))
        pygame.draw.circle(screen, (planet['color']), (planet_x, planet_y), planet_size)
        if planet['has_rings']:
            pygame.draw.circle(screen, (planet['color']), (planet_x, planet_y), int(planet_size*1.3), int(planet_size * 0.15))

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

        if setting_objs[0].value:
            for i in range(len(planet['old_positions']) - 1):
                pos = space_to_screen(planet['old_positions'][i], (t_camera_x, t_camera_y))
                pos2 = space_to_screen(planet['old_positions'][i + 1], (t_camera_x, t_camera_y))
                alpha = i / len(planet['old_positions']) * 255
                pygame.draw.line(surface, (150, 150, 180, alpha), pos, pos2, 2)
        else:
            screen_points = [space_to_screen(p, (t_camera_x, t_camera_y)) for p in planet['old_positions']]
            pygame.draw.lines(screen, (150, 150, 180), False, screen_points, 2)

        lpos = space_to_screen(planet['old_positions'][-1], (t_camera_x, t_camera_y))
        pygame.draw.line(screen, (150, 150, 180), lpos, (planet_x, planet_y), 2)
        screen.blit(surface, (0, 0))

    pygame.draw.rect(screen, (100, 100, 150), clock_rect)

    text = str(t.replace(microsecond=0))
    text_surface = clock_font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=clock_rect.center)
    screen.blit(text_surface, text_rect)

    pygame.draw.rect(screen, (20, 20, 30), pos_rect)

    text = "x{:.2e}".format(t_camera_x)+", y{:.2e}".format(t_camera_y)
    text_surface = clock_font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=pos_rect.center)
    screen.blit(text_surface, text_rect)

    following_color = planets[following]['color'] if following else (10, 10, 20)
    sidebar_color = ((following_color[0]+50)/6, (following_color[1]+50)/6, (following_color[2]+100)/6)
    pygame.draw.rect(screen, sidebar_color, sidebar)
    if following:
        text = following
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=name_rect.center)
        screen.blit(text_surface, text_rect)

        text = "Mass: {:.2e}".format(planets[following]['mass'])+"kg"
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midleft=mass_rect.midleft)
        screen.blit(text_surface, text_rect)

        text = "Radius: {:.2e}".format(planets[following]['radius'])+"km"
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midleft=radius_rect.midleft)
        screen.blit(text_surface, text_rect)

        velocity = planets[following]['velocity']
        text = "Velocity: x{:.2e}".format(velocity[0])+"km/s,"
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midleft=velocity_rect.midleft)
        screen.blit(text_surface, text_rect)

        text = "          y{:.2e}".format(velocity[1])+"km/s"
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(bottomleft=velocity_rect_y.bottomleft)
        screen.blit(text_surface, text_rect)

        delimage_rect = deleteimage.get_rect(topleft=delete_rect.topleft)
        screen.blit(deleteimage, delimage_rect)

        editimage_rect = editimage.get_rect(topleft=edit_rect.topleft)
        screen.blit(editimage, editimage_rect)

    if creating:
        pygame.draw.rect(screen, (30, 30, 50), create_rect)
        text = "Create Planet"
        text_surface = title_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=create_text_rect.center)
        screen.blit(text_surface, text_rect)
        for input_box in input_boxes:
            input_box.update()
            input_box.draw(screen)
        pygame.draw.rect(screen, (20, 90, 90), confirm_rect)
        text = "Confirm"
        text_surface = clock_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=confirm_rect.center)
        screen.blit(text_surface, text_rect)

        sel_color = (results[3], results[4], results[5])
        if is_color_valid(sel_color):
            pygame.draw.rect(screen, sel_color, color_rect)
        else:
            pygame.draw.rect(screen, (0,0,0), color_rect)
    elif settings_on:
        pygame.draw.rect(screen, (50, 50, 50), create_rect)
        text = "Settings"
        text_surface = title_font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=create_text_rect.center)
        screen.blit(text_surface, text_rect)
        for setting in setting_objs:
            setting.update()
            setting.draw()
    else:
        writing=False

def pause(pause=None):
    global paused, dt
    paused = not paused if pause is None else pause
    dt = 0 if paused else dt_scale if not real_time else 1/fps

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                for planet_name, planet in planets.items():
                    if math.hypot(mouse_x - space_to_screen(planet['position'])[0], mouse_y - space_to_screen(planet['position'])[1]) <= calculate_planet_size(planet['radius']) + 5:
                        launching = planet_name
                        pause(True)
                if camera_mode == 1 and not launching:
                    orig_space_mouse_x, orig_space_mouse_y = screen_to_space((mouse_x, mouse_y))
                    orig_camera_x, orig_camera_y = camera_x, camera_y
                    moving = True
                if following:
                    if delete_rect.collidepoint(mouse_x, mouse_y):
                        planets.pop(following)
                        following = ''
                if creating:
                    if confirm_rect.collidepoint(mouse_x, mouse_y):
                        for i, input_box in enumerate(input_boxes):
                            result = input_box.handle_event(event)
                            if (not input_box.acceptszero) and isinstance(result, int) and result == 0:
                                result=None
                            if result is not None:
                                results[i] = result
                        if all(r is not None for r in results):
                            planet_color = (results[3], results[4], results[5])
                            create_planet(results[0], results[1], results[2], planet_color ,creating_x, creating_y, results[6])
                            pause(False)
                            compute_frame(True)
                    elif not create_rect.collidepoint(mouse_x, mouse_y):
                        if all(not box.active for box in input_boxes):
                            creating = False
                            pause(False)
                elif settings_on:
                    if not create_rect.collidepoint(mouse_x, mouse_y):
                        settings_on = False
                        pause(False)
            elif event.button == 3:
                mouse_x, mouse_y = event.pos
                for planet_name, planet in planets.items():
                    if math.hypot(mouse_x - space_to_screen(planet['position'])[0], mouse_y - space_to_screen(planet['position'])[1]) <= calculate_planet_size(planet['radius']) + 5:
                        camera_mode = 1
                        camera_x, camera_y = planet['position']
                        following = planet_name
                        print(following)
                    elif following == planet_name:
                        following = None
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if launching:
                    mouse_x, mouse_y = event.pos
                    space_mouse_x, space_mouse_y = screen_to_space((mouse_x, mouse_y))
                    planets[launching]['velocity'] = np.array([(planets[launching]['position'])[0] - space_mouse_x, planets[launching]['position'][1] - space_mouse_y]) / 30000
                    launching = ''
                    pause(False)
                moving = False
        elif event.type == pygame.MOUSEWHEEL:
            if camera_mode == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                zoom_factor = min(100000,max(0.001, zoom_factor * (1 + event.y * 0.1)))
                #camera_x, camera_y = kmpx_ratio * 2 * (mouse_x - 1000) /2+camera_x, kmpx_ratio * 2 * (mouse_y - 1000) /2-camera_y
        elif event.type == pygame.KEYDOWN:
            if not writing:
                if event.key == pygame.K_c:
                    camera_mode = 1 if camera_mode == 0 else 0
                    following = ''
                elif event.key == pygame.K_SPACE:
                    pause()
                    if frame_count % 2 == 0:
                        for planet_name, planet in planets.items():
                            planet['old_positions'].append(planet['position'])
                elif event.key == pygame.K_r:
                    real_time = not real_time
                    dt = 1/fps if real_time else dt_scale
                elif event.key == pygame.K_p:
                    real_sizes = not real_sizes
                elif event.key == pygame.K_q:
                    creating_x, creating_y = screen_to_space(pygame.mouse.get_pos())
                    pause(True)
                    creating = True
                elif event.key == pygame.K_d:
                    for planet_name, planet in planets.items():
                        planet['old_positions'] = [planet['position']]
                elif event.key == pygame.K_s:
                    settings_on = not settings_on
                    pause(settings_on)
        if creating:
            for i, input_box in enumerate(input_boxes):
                result=input_box.handle_event(event)
                if (not input_box.acceptszero) and (type(result) ==int) and result == 0:
                    result = None
                if result is not None:
                    results[i] = result
        if settings_on:
            for i, setting in enumerate(setting_objs):
                result=setting.handle_event(event)
                if result is not None:
                    settings[0]=result
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