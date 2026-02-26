import pygame as pygame
import numpy as np
import random

pygame.init()
mainclock = pygame.time.Clock()

# --- variables ---
screen_height = 600
screen_width = 800
screen = pygame.display.set_mode((screen_width, screen_height)) 

theme_text   = (0, 0, 0)
theme_muted   = (150,150,150)
theme_fg  = (197, 197, 197)
theme_bg   = (255, 255, 255)
theme_success = (166, 209, 137)
theme_danger  = (226, 117, 117)

run = True
direction = True
block_size = 5
chunk_size = 10

font = pygame.font.SysFont(None, 24)
pygame.display.set_caption("Sand Simulator 3000")

overlay_h = 50
overlay_rect = pygame.Rect(0, 0, screen_width, overlay_h)

grid_height = (screen_height - overlay_h) // block_size
grid_width  = screen_width // block_size
grid_rect = pygame.Rect( 0, overlay_h, screen_width, screen_height - overlay_h)

grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 3), dtype=np.uint8)

grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

active_chunk = np.zeros((grid_width // chunk_size, grid_height // chunk_size), dtype=bool)
active_chunk_next = np.zeros((grid_width // chunk_size, grid_height // chunk_size), dtype=bool)

neighbors_offset = [(-1, -1), (0, -1), (1, -1),(-1,  0), (1,  0), (-1,  1), (0,  1), (1,  1)]

# --- user variable ---
grid_x = 0 
grid_y = 0

mouse_x = 0
mouse_y = 0

selected_block = 1
hovered_block = 0

debug_mode = False
game_paused = False
mouser_pressed = False
hovering_button = False

tooltip_text = None

# --- blocks ---

blocks = {
    0: { "name": "Void",  "color": (255, 255, 255), 
        "density": 0, "state": "solid", "ability": None},
    1: { "name": "sand",  "color": (194, 178, 128), 
        "density": 4, "state": "grain", "ability": None},
    2: { "name": "stone", "color": (110, 110, 110), 
        "density": 6, "state": "solid", "ability": None},
    3: { "name": "water", "color": (64, 164, 223), 
        "density": 2, "state": "liquid", "ability": None},
    4: { "name": "acid",  "color": (57, 255, 20), 
        "density": 9, "state": "liquid", "ability": "destroy"},
    5: { "name": "steam", "color": (220, 220, 220), 
        "density": 0, "state": "gas", "ability": None}}

# --- brush ---

create_brush = lambda r : [(x,y) for x in range(-r, r+1) for y in range(-r, r+1) if x*x + y*y <= r*r]
brushes = {'S': create_brush(2), 'M': create_brush(4), 'L': create_brush(6)}
selected_brush = 'S'

# --- block_palette ---

def create_block_palette(delta=8, count=8):
    return {
        block: [
            tuple(
                max(0, min(255, c + random.randint(-delta, delta)))
                for c in data['color'])
            for _ in range(count)]
        for block, data in blocks.items()
    }

block_palette = create_block_palette()

# --- Classes ---

class Radiogroup:
    def __init__(self, groupname):
        self.groupname = groupname
        self.radios = []

    def add(self, radio):
        self.radios.append(radio)

    def select(self, selected_radio):

        for radio in self.radios:
            radio.toggled = False
        
        selected_radio.toggled = True

class Button:
    def __init__(self, rect = None, circle = None, action=None, label='', color= (255,255,255),text_color = (0,0,0) ,
                 toggled=None, group=None, shortcut=None, tooltip_text=None):

        self.rect = rect

        self.action = action
        self.label = label
        
        self.color = color 
        self.text_color = text_color

        self.toggled = toggled   
        self.group = group

        self.shortcut = shortcut
        self.tooltip_text = tooltip_text

        self.temp_circle = self.rect.height//2

        if self.group is not None:
            self.group.add(self)

        self.font = pygame.font.SysFont(None, 24)
        self.clicked = False
        self.hovered = False

    def handle_draw(self):
        state = self.get_state()

        if state == "active":
            self.draw_active()
        elif state == "hover":
            self.draw_hover()
        else:
            self.draw_normal()

    def get_state(self):
        if self.toggled or self.clicked:
            return "active"
        if self.hovered:
            return "hover"
        return "normal"
    
    def draw_normal(self):
        pygame.draw.rect(screen, self.color, self.rect,border_radius=50)
        self.draw_label(self.text_color)

    def draw_hover(self):
        pygame.draw.rect(screen, self.color, self.rect,border_radius=50)
        pygame.draw.rect(screen, self.text_color, self.rect, 1,border_radius=50)
        self.draw_label(self.text_color)

    def draw_active(self):
        pygame.draw.rect(screen, self.text_color, self.rect,border_radius=50)
        self.draw_label(self.color)

    def draw_label(self, color):
        label = self.font.render(self.label, True, color)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_hover(self):
        self.hovered = self.rect.collidepoint((mouse_x, mouse_y))
        if self.hovered and self.tooltip_text:
            global tooltip_text
            tooltip_text = f"{self.tooltip_text}"
        return self.hovered

    def handle_event(self, event):
        # mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_x, mouse_y):
                self.activate()

        # keyboard shortcut
        elif event.type == pygame.KEYDOWN:
            if self.shortcut and event.key == self.shortcut:
                self.activate()
    
    def activate(self):
        # group controls toggling
        if self.group:
            self.group.select(self)

        # standalone toggle
        elif self.toggled is not None:
            self.toggled = not self.toggled

        if self.action:
            self.action()

class CircleButton(Button):
    def draw_normal(self):
        pygame.draw.circle(screen, self.color, self.rect.center, self.temp_circle)
        # pygame.draw.circle(screen, self.text_color, self.rect.center, self.temp_circle,1)
        self.draw_label(self.text_color)

    def draw_hover(self):
        pygame.draw.circle(screen,self.color,self.rect.center, self.temp_circle)
        pygame.draw.circle(screen,self.text_color,self.rect.center, self.temp_circle , 1)
        self.draw_label(self.text_color)

    def draw_active(self):
        pygame.draw.circle(screen,self.color,self.rect.center, self.temp_circle)
        pygame.draw.circle(screen,self.text_color,self.rect.center, self.temp_circle , 2)
        self.draw_label(self.text_color)

# --- btns funstions ---

def pause_game():
    global game_paused
    game_paused = not game_paused

def toggle_debug():
    global debug_mode
    debug_mode = not debug_mode

def Reset():
    grid_value.fill(0)
    grid_color.fill(0)

def set_brush(index):
    global selected_brush
    selected_brush = index

def set_selected_block(block_id):
    global selected_block
    selected_block = block_id

# --- Adding btns ---
button_list = []

padding = 4
main_padding = 24

h = 26
x = padding
y = overlay_h // 2 - h // 2


# --- action buttons ---
action_buttons = [
    ("Pause", pause_game, False, pygame.K_SPACE, "Pause the game (Space)"),
    ("Debug", toggle_debug, False, pygame.K_d, "Toggle debug mode (D)"),
    ("Reset", Reset, None, pygame.K_BACKSPACE, "Reset the game (Backspace)"),
]

for label, action, toggled, shortcut, tooltip in action_buttons:
    w = font.size(label)[0] + 16
    button_list.append(
        Button(
            rect=pygame.Rect(x, y, w, h),
            action=action,
            label=label,
            toggled=toggled,
            color=theme_muted,
            shortcut=shortcut,
            tooltip_text=tooltip,
        )
    )
    x += w + 4

x += main_padding

# --- block selection ---
block_group = Radiogroup("block_group")
for block_id, block in blocks.items():
    button_list.append(
        CircleButton(
            rect=pygame.Rect(x, y, 16, h),
            action=lambda b=block_id: set_selected_block(b),
            label=str(block_id),
            color=block["color"],
            toggled=(selected_block == block_id),
            group=block_group,
            shortcut=pygame.K_0 + block_id,
            tooltip_text=f"Select {block['name'].capitalize()} ({block_id})" 
        )
    )
    x += h + padding

x += main_padding

# --- brush selection ---
brush_group = Radiogroup("brush_group")

for key in brushes:
    shortcut = {"S": pygame.K_s, "M": pygame.K_m, "L": pygame.K_l}[key]
    button_list.append(
        CircleButton(
            rect=pygame.Rect(x, y, 16, h),
            action=lambda r=key: set_brush(r),
            label=str(key),
            color=theme_muted,
            toggled=(selected_brush == key),
            group=brush_group,
            shortcut=shortcut,
            tooltip_text=f"Select brush size ({key.capitalize()})"
        )
    )
    x += h + padding

# --- Small helpers ---
get_close_color = lambda block : random.choice(block_palette[block])

calculate_padding = lambda lines ,font_size=16 : (font_size + font_size/3) * lines

def get_grid_cords():
    global grid_x, grid_y

    # ignore overlay area
    if mouse_y < overlay_h:
        return grid_x, grid_y

    temp_grid_x = mouse_x // block_size
    temp_grid_y = (mouse_y - overlay_h) // block_size

    if 0 <= temp_grid_x < grid_width and 0 <= temp_grid_y < grid_height:
        grid_x = temp_grid_x
        grid_y = temp_grid_y

    return grid_x, grid_y

# --- Draw helpers ---

def draw_text(text, x, y, color=theme_muted):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


# --- chunking ---











def activate_chunk(x,y):
    chunk_x = int(x // chunk_size)
    chunk_y = int(y // chunk_size)

    if 0 <= chunk_x < active_chunk.shape[0] and 0 <= chunk_y < active_chunk.shape[1]:
        active_chunk[chunk_x, chunk_y] = True

def deactivate_chunk(x,y):
    chunk_x = int(x // chunk_size)
    chunk_y = int(y // chunk_size)

    if 0 <= chunk_x < active_chunk.shape[0] and 0 <= chunk_y < active_chunk.shape[1]:
        active_chunk[chunk_x, chunk_y] = False

def is_chunk_active(x, y):
    chunk_x = int(x // chunk_size)
    chunk_y = int(y // chunk_size)
    if 0 <= chunk_x < active_chunk.shape[0] and 0 <= chunk_y < active_chunk.shape[1]:
        return active_chunk[chunk_x, chunk_y]
    return False



def draw_chunks(color=theme_muted):
    for chunk_x in range(active_chunk.shape[0]):
        for chunk_y in range(active_chunk.shape[1]):
            x = chunk_x * chunk_size * block_size
            y = overlay_h + chunk_y * chunk_size * block_size
            if active_chunk[chunk_x, chunk_y]:
                pygame.draw.rect(screen, theme_danger, pygame.Rect(x, y, chunk_size * block_size, chunk_size * block_size), 1)
            else:
                pygame.draw.rect(screen, theme_success, pygame.Rect(x, y, chunk_size * block_size, chunk_size * block_size), 1)





















# --- Simulation ---
def mark_in_active_grid(x, y):
    for dx, dy in neighbors_offset:
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            if grid_value[mx,my]:
                grid_active_next[mx, my] = True
    
                activate_chunk(x, y)

def swap(x, y, x1, y1):  
    grid_value[x, y], grid_value[x1, y1] = \
    grid_value[x1, y1], grid_value[x, y]

    grid_color[x, y], grid_color[x1, y1] = \
    grid_color[x1, y1].copy(), grid_color[x, y].copy()

    mark_in_active_grid(x, y)
    mark_in_active_grid(x1, y1)

def destroy(x, y, x1, y1):
    grid_value[x1, y1] = 0
    grid_color[x1, y1] = (0,0,0)

    grid_value[x, y] = 0
    grid_color[x, y] = (0,0,0)

    mark_in_active_grid(x, y)
    mark_in_active_grid(x1, y1)

def move(x, y, dx=0, dy=0):
    mx, my = x + dx, y + dy

    if not (0 <= mx < grid_width and 0 <= my < grid_height):
        return False

    target_val = grid_value[mx, my]
    current_val = grid_value[x, y]

    if target_val == 0:
        swap(x, y, mx, my)
        return True

    current_denser = blocks[current_val]['density'] > blocks[target_val]['density']
    if current_denser:

        if blocks[current_val]['ability'] == 'destroy':
            destroy(x, y, mx, my)
            return True

        # Standard Density Swap (sand swaps water)
        swap(x, y, mx, my)
        return True

    return False

def place_block(x, y):
    if not grid_value[grid_x, grid_y] or not selected_block:
        grid_value[grid_x, grid_y] = selected_block
        grid_color[grid_x, grid_y] = get_close_color(selected_block)
        mark_in_active_grid(grid_x,grid_y)

    # add neighbour
    for dx, dy in brushes[selected_brush]:
        if random.randint(0, 4) == 0:continue
        
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            mark_in_active_grid(mx,my)
            neighbors_color = get_close_color(selected_block)
            if not grid_value[mx, my] or not selected_block:
                grid_value[mx, my] = selected_block
                grid_color[mx, my] = neighbors_color

# direct draw helper of game
def draw_block(x,y):
    screen_y = overlay_h + block_size * y
    screen_x = block_size * x 

    # block
    if not grid_color[x, y].all():
        grid_color[x, y] = get_close_color(grid_value[x, y])
    
    # draw
    if debug_mode and grid_active[x, y]
    :
        pygame.draw.rect(screen, grid_color[x, y], pygame.Rect(screen_x, screen_y, block_size, block_size),2)
    else:
        pygame.draw.rect(screen, grid_color[x, y], pygame.Rect(screen_x, screen_y, block_size, block_size))

# simple abbrevation functions
move_up  = lambda x,y : move(x,y,0,-1)
move_up_left  = lambda x,y : move(x,y,-1,-1)
move_up_right = lambda x,y : move(x,y,1,-1)
move_left  = lambda x,y : move(x,y,-1,0)
move_right = lambda x,y : move(x,y,1,0)
move_down  = lambda x,y : move(x,y,0,1)
move_down_left  = lambda x,y : move(x,y,-1,1)
move_down_right = lambda x,y : move(x,y,1,1)

# direct simulate helper of game
def simulation_block(x, y):
    block = blocks[grid_value[x, y]]
    state = block['state']
    
    if not grid_active[x, y]:
        return

    # Solid (Stone) doesn't move
    if state == 'solid':
        return

    # Grain (Sand) logic: Down, then Down-Diagonal
    if state == 'grain':
        if move_down(x, y): return
        if direction:
            if move_down_right(x, y): return
            if move_down_left(x, y): return
        else:
            if move_down_left(x, y): return
            if move_down_right(x, y): return

    # Liquid (Water/Acid) logic: Down, Down-Diagonal, then Horizontal
    elif state == 'liquid':
        if move_down(x, y): return
        if direction:
            if move_down_right(x, y) or move_right(x, y): return
            if move_down_left(x, y) or move_left(x, y): return
        else:
            if move_down_left(x, y) or move_left(x, y): return
            if move_down_right(x, y) or move_right(x, y): return
        if state == 'liquid' and block['ability'] == 'destroy':
            move_up(x, y)

    # Gas (Steam) logic: Up, then Up-Diagonal or Horizontal
    elif state == 'gas':
        if move_up(x, y): return
        if direction:
            if move_up_right(x, y) or move_right(x, y): return
            if move_up_left(x, y) or move_left(x, y): return
        else:
            if move_up_left(x, y) or move_left(x, y): return
            if move_up_right(x, y) or move_right(x, y): return

# right
def game():
    pygame.draw.rect(screen, theme_bg, grid_rect)

    # Placement logic
    if grid_rect.collidepoint(mouse_x, mouse_y) and mouser_pressed:
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:           
            place_block(grid_x,grid_y)

    # loop bottom to top
    for y in range(grid_height - 1, -1, -1):
        x_order = list(range(grid_width))
        random.shuffle(x_order)

        for x in x_order:
            if grid_value[x, y]:
                # draw
                if is_chunk_active(x,y):595
                    draw_block(x, y)

                # Simulation
                if not game_paused:
                    simulation_block(x, y)
    
    draw_chunks(color=theme_muted)
    
# --- Main loop ---
while run:   
    # --- Variables ---
    tooltip_text = None
    mouse_clicked = False
    direction = not direction  # not sure if you need to toggle every frame
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = get_grid_cords()

    
    
    # --- Event handling ---
    for event in pygame.event.get():
        # handle buttons
        for btn in button_list:
            btn.handle_event(event)
        
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouser_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            mouser_pressed = False 

    # --- Draw ---
    game() 

    # Overlay UI
    pygame.draw.rect(screen, theme_fg, overlay_rect)
    pygame.draw.line(screen, theme_text, (0, overlay_h), (screen_width, overlay_h))
    
    # FPS
    fps_text = f"FPS {int(mainclock.get_fps())}"
    screen.blit(
        font.render(fps_text, True, theme_text),
        (screen_width - font.size(fps_text)[0] - 8, (overlay_h - font.size(fps_text)[1]) // 2)
    )

    # --- Update active blocks ---
    if not game_paused:
        grid_active[:] = grid_active_next
        grid_active_next.fill(False)

        active_chunk[:] = active_chunk_next
        active_chunk_next.fill(False)

    # --- Buttons ---
    hovering_button = False
    for btn in button_list:
        btn.handle_draw()
        if btn.handle_hover():  # handle_hover should return True if hovered
            hovering_button = True
            if btn.tooltip_text:
                tooltip_text = btn.tooltip_text  # set tooltip for hovered button

    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hovering_button else pygame.SYSTEM_CURSOR_ARROW)

    # --- Tooltips ---
    if tooltip_text:
        text_w, text_h = font.size(tooltip_text)
        tooltip_rect = pygame.Rect(mouse_x + 16, mouse_y + 16, text_w + 24, text_h + 8)
        pygame.draw.rect(screen, theme_text, tooltip_rect, border_radius=6)
        screen.blit(font.render(tooltip_text, True, theme_bg), tooltip_rect.topleft + pygame.Vector2(12, 4))

    # --- Update screen ---
    pygame.display.update()
    mainclock.tick(60)














# Simple screenshake manager (Pygame)
class ScreenShake:
    def __init__(self):
        self.time = 0.0
        self.duration = 0.0
        self.magnitude = 0.0

    def start(self, duration, magnitude):
        self.time = 0.0
        self.duration = duration
        self.magnitude = magnitude

    def update(self, dt):
        if self.time < self.duration:
            self.time += dt
            t = self.time / self.duration
            # ease out (quadratic)
            decay = (1 - t) * (1 - t)
            import random
            x = (random.random() * 2 - 1) * self.magnitude * decay
            y = (random.random() * 2 - 1) * self.magnitude * decay
            return int(x), int(y)
        return 0, 0

# Usage in main loop:
# shake.start(0.18, 8)
# offset_x, offset_y = shake.update(dt)
# screen.blit(world_surface, (offset_x, offset_y))

import pygame, random, math

class Particle:
    def __init__(self, pos, vel, life, color, size):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.life = life
        self.max_life = life
        self.text_color = color
        self.size = size

    def update(self, dt):
        self.pos += self.vel * dt
        self.life -= dt
        # simple drag
        self.vel *= 0.98

    def draw(self, surf):
        alpha = max(0, int(255 * (self.life / self.max_life)))
        col = (*self.text_color[:3], alpha)
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (self.size, self.size), self.size)
        surf.blit(s, (self.pos.x - self.size, self.pos.y - self.size))

# Emitter example: spawn N particles with random velocity
def emit_explosion(container, pos, n=30):
    for _ in range(n):
        angle = random.random() * math.tau
        speed = random.uniform(60, 240)
        vel = (math.cos(angle)*speed, math.sin(angle)*speed)
        p = Particle(pos, vel, life=0.8 + random.random()*0.6, color=(255,160,64), size=random.randint(2,5))
        container.append(p)

# apply a quick scale animation to a sprite surface
def squash_stretch(surface, progress, max_scale=1.12):
    # progress: 0..1 where 0 is start, 1 is end
    # ease out
    t = 1 - (1 - progress) * (1 - progress)
    sx = 1 + (max_scale - 1) * (1 - t)
    sy = 1 - (max_scale - 1) * (1 - t) * 0.6
    w, h = surface.get_size()
    scaled = pygame.transform.smoothscale(surface, (int(w*sx), int(h*sy)))
    return scaled