import pygame as pygame
import numpy as np
import random

pygame.init()
mainclock = pygame.time.Clock()

# --- display variables ---
screen_size= 600
overlay_size = 200

screen_height = screen_size
screen_width = screen_size + overlay_size

screen = pygame.display.set_mode((screen_width, screen_height)) 

# --- theme variables ---
theme_text   = (0, 0, 0)
theme_muted   = (197, 197, 197)
theme_bg   = (255, 255, 255)

theme_success = (166, 209, 137)
theme_danger  = (226, 117, 117)

# --- game variables ---
run = True
direction = True
block_size = 5
chunk_size = block_size * 10

font = pygame.font.SysFont(None, 24)

overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)

grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
grid_rect = pygame.Rect(overlay_size,0,screen_width - overlay_size,screen_height)

grid_value  = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 3), dtype=np.uint8)

grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

neighbors_offset = [(-1, -1), (0, -1), (1, -1), (-1,  0), (1,  0), (-1,  1), (0,  1), (1,  1)]

# --- user variable ---
grid_x = 0 
grid_y = 0

mouse_x = 0
mouse_y = 0

selected_block = 1
hovered_block = 0

debug_mode = False
game_paused = False
mouse_clicked = False
mouser_pressed = False
hovering_button = False

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
brushes = [create_brush(2),create_brush(4),create_brush(6),create_brush(8)]
current_brush = 1

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
    def __init__(self, rect, action=None, label='',
                 text_color=(0,0,0), bg_color=(255,255,255), border_color=(150,150,150),
                toggled=None, group=None,value = None):

        self.rect = rect
        self.label = label
        self.action = action
        
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color

        self.toggled = toggled   
        self.group = group

        self.value = value or self.rect.height//2

        if self.group is not None:
            self.group.add(self)

        self.font = pygame.font.SysFont(None, 24)
        self.clicked = False
        self.hovered = False

    
    def handle_draw(self):
        state = self.get_state()

        if state == "active":
            self.draw_active()
        elif state == "pressed":
            self.draw_pressed()
        elif state == "hover":
            self.draw_hover()
        else:
            self.draw_normal()

    def get_state(self):
        if self.toggled:
            return "active"
        if self.clicked:
            return "pressed"
        if self.hovered:
            return "hover"
        return "normal"
    

    def draw_normal(self):
        pygame.draw.rect(screen, self.border_color, self.rect, 1,border_radius=5)
        self.draw_label(self.text_color)

    def draw_hover(self):
        pygame.draw.rect(screen, self.border_color, self.rect, 3,border_radius=5)
        self.draw_label(self.text_color)

    def draw_active(self):
        pygame.draw.rect(screen, self.text_color, self.rect,border_radius=5)
        self.draw_label(self.bg_color)

    def draw_pressed(self):
        pygame.draw.rect(screen, self.text_color, self.rect,border_radius=5)
        self.draw_label(self.bg_color)

    def draw_label(self, color):
        label = self.font.render(self.label, True, color)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_hover(self):
        self.hovered = self.rect.collidepoint((mouse_x, mouse_y))
        return self.hovered

    def handle_event(self):
        if not self.rect.collidepoint(mouse_x, mouse_y):
            return

        # group controls toggling
        if self.group:
            self.group.select(self)

        # standalone toggle button
        elif self.toggled is not None:
            self.toggled = not self.toggled

        # default
        if self.action:
            self.action()


class CircleButton(Button):
    def draw_normal(self):
        pygame.draw.circle(screen, self.text_color, self.rect.center, self.value)
        pygame.draw.circle(screen, self.border_color, self.rect.center, self.value,1)

    def draw_hover(self):
        pygame.draw.circle(screen,self.text_color,self.rect.center, self.value - 1)
        pygame.draw.circle(screen,self.border_color,self.rect.center, self.value + 2, 1)

    def draw_active(self):
        pygame.draw.circle(screen,self.text_color,self.rect.center, self.value - 1)
        pygame.draw.circle(screen,(0,0,0),self.rect.center, self.value + 2, 1)


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
    global current_brush
    current_brush = index

def set_selected_block(block_id):
    global selected_block
    selected_block = block_id


# --- Adding btns ---
button_list = []
btn_height = 30

# action buttons 
start_y = 30
columns = 3
cell_width = overlay_size // columns

buttons = [
    ("Pause", pause_game, False),
    ("Debug", toggle_debug, False),
    ("Reset", Reset, None),
]

for i, (label, action, toggled) in enumerate(buttons):
    button_list.append(
        Button(
            rect=pygame.Rect(i * cell_width, start_y, cell_width, btn_height),
            action=action,
            label=label,
            toggled=toggled,
            text_color=theme_text,
            bg_color=theme_bg,
        )
    )

# block selection 
start_y += btn_height * 2
columns = 5
cell_width = overlay_size // columns
gap = 5

block_group = Radiogroup("block_group")

for i, block_id in enumerate(blocks):
    x = (i % columns) * cell_width
    y = start_y + (i // columns) * (btn_height + gap)

    button_list.append(
        CircleButton(
            rect=pygame.Rect(x, y, cell_width, btn_height),
            action=lambda b=block_id: set_selected_block(b),
            label=blocks[block_id]["name"].capitalize(),
            text_color=blocks[block_id]["color"],
            bg_color=theme_bg,
            toggled=(selected_block == block_id),
            group=block_group
        )
    )

# brush selection 
start_y += btn_height * 3
brush_group = Radiogroup("brush_group")

x = 8
gap = 8

for radius in range(len(brushes) -1,-1,-1):
    size = block_size * (radius + 1)
    w = size * 1.8

    if x + w > overlay_size:
        break

    button_list.append(
        CircleButton(
            rect=pygame.Rect(x, start_y, w, btn_height),
            action=lambda r=radius: set_brush(r),
            value=size,
            text_color=theme_text,
            bg_color=theme_bg,
            toggled=(current_brush == radius),
            group=brush_group
        )
    )

    x += w + gap


# --- Small helpers ---
get_close_color = lambda block : random.choice(block_palette[block])

calculate_padding = lambda lines ,font_size=16 : (font_size + font_size/3) * lines

def get_grid_cords():
    global grid_x, grid_y
    
    adjusted_x = mouse_x - overlay_size
    
    temp_grid_x = int(adjusted_x / block_size)
    temp_grid_y = int(mouse_y / block_size)

    if 0 <= temp_grid_x < grid_width and  0 <= temp_grid_y < grid_height:
        grid_x = temp_grid_x
        grid_y = temp_grid_y
    
    return grid_x, grid_y

# --- Draw helpers ---

def draw_text(text, x, y, color=theme_muted):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_chunks(color = theme_muted):
    for x in range(grid_rect.left, screen_width + 1, chunk_size):
        pygame.draw.line(screen, color, (x, 0), (x, screen_height))
        
    for y in range(0, screen_height + 1, chunk_size):
        pygame.draw.line(screen, color, (grid_rect.left, y), (screen_width, y))

# --- Simulation ---
def mark_in_active_grid(x, y):
    for dx, dy in neighbors_offset:
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            if grid_value[mx,my]:
                grid_active_next[mx, my] = True

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
    for dx, dy in brushes[current_brush]:
        if random.randint(0, 1): continue
        
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            mark_in_active_grid(mx,my)
            neighbors_color = get_close_color(selected_block)
            if not grid_value[mx, my] or not selected_block:
                grid_value[mx, my] = selected_block
                grid_color[mx, my] = neighbors_color

# direct draw helper of game
def draw_block(x,y):
    screen_y = block_size * y
    screen_x = overlay_size + block_size * x 

    # block
    if not grid_color[x, y].all():
        grid_color[x, y] = get_close_color(grid_value[x, y])
    
    # block
    

    # draw
    if debug_mode and grid_active[x, y]:
        pygame.draw.rect(screen, grid_color[x, y], pygame.Rect(screen_x, screen_y, block_size, block_size),1)
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
                draw_block(x, y)

                # Simulation
                if not game_paused:
                    simulation_block(x, y)
    
    # debug_mode
    if debug_mode:
        draw_chunks(color=theme_muted)
        pygame.draw.circle(screen, theme_muted, (mouse_x, mouse_y), block_size * (current_brush + 1), 1)
    
# left 
def overlay():
    pygame.draw.rect(screen, theme_bg, overlay_rect)

    pygame.draw.line(screen, theme_muted, [overlay_size, 0], [overlay_size, screen_height],3)
    
    draw_text(f'FPS {int(mainclock.get_fps())}', 8, screen_height - 72)   
    draw_text(f"X {mouse_x:03d} Y {mouse_y:03d}", 8, screen_height - 48)
    draw_text(f"Cells {np.count_nonzero(grid_active):05d} / {np.count_nonzero(grid_value):05d}", 8, screen_height - 24) 



# main loop
pygame.display.set_caption("Sand Simulator - by Chitesh Malhotra")
# pygame.draw.rect(screen, theme_bg, screen.get_rect())
while run:   
    # --- event loop ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_clicked = True
            mouser_pressed = True

        elif event.type == pygame.MOUSEBUTTONUP:
            mouser_pressed = False

        elif event.type == pygame.KEYDOWN:

            key_num = event.key - pygame.K_0
            if key_num in blocks:
                selected_block = key_num

            if event.key in [pygame.K_SPACE,pygame.K_RETURN]:
                game_paused = not game_paused
    
    # --- Main partation ---
    game()
    overlay()

    # --- active blocks update ---
    if not game_paused:
        grid_active[:] = grid_active_next
        grid_active_next.fill(False)

    # --- Button ---
    for btn in button_list:
        btn.handle_draw()
        if mouse_clicked:
            btn.handle_event()

        if btn.handle_hover():
            hovering_button = True
        
    # --- other tasks ---
    cursor = pygame.SYSTEM_CURSOR_HAND if hovering_button else pygame.SYSTEM_CURSOR_ARROW
    pygame.mouse.set_cursor(cursor)

    # --- Variables ---
    mouse_clicked = False
    hovering_button = False
    direction = not direction
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = get_grid_cords()

    # --- update screen ---
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