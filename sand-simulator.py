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

# --- color variables ---
black   = (0, 0, 0)
grey    = (90, 90, 90)
muted   = (197, 197, 197)
white   = (240, 240, 240)
success = (166, 209, 137)
danger  = (226, 117, 117)

# --- theme variables ---
night_theme = {'bg': black,'fg': grey, 'muted': muted, 'text': white, 'success': success,'danger':danger}
light_theme = {'bg': white, 'fg': muted, 'muted': grey, 'text': black, 'success': success,'danger':danger}

# --- game variables ---
run = True
direction = True
block_size = 5

overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)

grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
grid_rect = pygame.Rect(overlay_size,0,screen_width - overlay_size,screen_height)

grid_value  = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 3), dtype=np.uint8)
grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

font = pygame.font.SysFont(None, 24)

# --- user variable ---

game_paused = False
draw_grid = False
hovering_button = False

grid_x = 0 
grid_y = 0

mouse_x = 0
mouse_y = 0

selected_block = 1

mouse_clicked = False
mouser_pressed = False

logs = ["No logs yet"]
current_theme = light_theme

# neighbour
neighbors_offset = [
    (-1, -1), (0, -1), (1, -1), 
    (-1,  0), (0,  0), (1,  0), 
    (-1,  1), (0,  1), (1,  1)
]

# --- blocks ---
blocks = {
    0: {
        "name": "Void",
        "color": current_theme["bg"],  # natural sand beige
        "density": 0,
        "state": "solid",
        "ability": None,
    },
    1: {
        "name": "sand",
        "color": (194, 178, 128),  # natural sand beige
        "density": 4,
        "state": "grain",
        "ability": None,
    },

    2: {
        "name": "stone",
        "color": (110, 110, 110),  # medium stone gray
        "density": 6,
        "state": "solid",
        "ability": None,
    },

    3: {
        "name": "water",
        "color": (64, 164, 223),  # clean water blue
        "density": 2,
        "state": "liquid",
        "ability": None,
    },

    4: {
        "name": "acid",
        "color": (57, 255, 20),  # toxic neon green
        "density": 9,
        "state": "liquid",
        "ability": "destroy",
    },

    5: {
        "name": "steam",
        "color": (220, 220, 220),  # soft light gray (avoid alpha issues)
        "density": 0,
        "state": "gas",
        "ability": None,
    },
}


# brush
def initilize_brush(radius):
    return [(x, y)
            for x in range(-radius, radius + 1)
            for y in range(-radius, radius + 1)
            if x*x + y*y <= radius*radius]

brushes = {
    "XS": initilize_brush(0),
    "S": initilize_brush(1),
    "M": initilize_brush(2),
    "L": initilize_brush(3),
    "XL": initilize_brush(4),
}

current_brush_label = "M"
current_brush = brushes[current_brush_label]

# palette
def initilize_palette(delta = 8,count = 8):
    complete_palette={}
    for block in blocks.keys():
        r, g, b = blocks[block]['color']

        single_block_palette = []
        for _ in range(count):
            single_block_palette.append((
                max(0, min(255, r + random.randint(-delta, delta))),
                max(0, min(255, g + random.randint(-delta, delta))),
                max(0, min(255, b + random.randint(-delta, delta))),
            ))
        complete_palette[block] = single_block_palette
    return complete_palette

palette = initilize_palette()


# --- btn class ---
class Radiogroup:
    def __init__(self, groupname):
        self.groupname = groupname
        self.radios = []

    def add(self, radio):
        self.radios.append(radio)

    def select(self, selected_radio):

        # If only one radio → behave like toggle
        if len(self.radios) == 1:
            selected_radio.toggled = not selected_radio.toggled
            return

        # Normal radio behaviour
        for radio in self.radios:
            radio.toggled = False

        selected_radio.toggled = True

class Base_button:
    def __init__(self, rect, action=None, label='', 
                 text_color=(0,0,0), bg_color=(255,255,255),
                 toggled=None, group=None):

        self.rect = rect
        self.label = label
        self.action = action
        self.bg = bg_color or current_theme["bg"]
        self.color = text_color or current_theme["text"]

        self.toggled = toggled   
        self.group = group

        if self.toggled is not None and self.group:
            self.group.add(self)

        self.font = pygame.font.SysFont(None, 24)
        self.clicked = False
        self.hovered = False


    def handle_draw(self):
        if self.toggled is None:
            self.draw_normal()
        else:
            self.draw_toggle()


    def draw_normal(self):
        bg = get_reduced_color(self.bg) if self.hovered else self.bg
        text_color = self.color
        border_color = current_theme["text" if self.hovered or self.toggled else "fg"]

        pygame.draw.rect(screen, bg, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)

        label = self.font.render(self.label, True, text_color)
        screen.blit(label, label.get_rect(center=self.rect.center))


    def draw_toggle(self):
        bg = get_reduced_color(self.bg) if self.toggled else self.bg
        text_color = self.color

        border_color = current_theme["text" if self.hovered or self.toggled else "fg"]

        pygame.draw.rect(screen, bg, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)

        label = self.font.render(self.label, True, text_color)
        screen.blit(label, label.get_rect(center=self.rect.center))


    def handle_hover(self):
        self.hovered = self.rect.collidepoint((mouse_x, mouse_y))
        return self.hovered


    def handle_event(self):
        if self.rect.collidepoint(mouse_x,mouse_y):

            # Normal button
            if self.toggled is None:
                self.clicked = not self.clicked
                if self.action:
                    self.action()

            # Radio button
            else:
                self.group.select(self)
                if self.action:
                    self.action()

# --- btn funstions ---
def pause_game():
    global game_paused
    game_paused = not game_paused

def toggle_theme():
    global current_theme
    current_theme = light_theme if current_theme == night_theme else night_theme

def toggle_grid():
    global draw_grid
    draw_grid = not draw_grid

def Reset():
    global grid_value,grid_color
    grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
    grid_color = np.zeros((grid_width, grid_height, 3), dtype=np.uint8)

def set_brush(label):
    global current_brush, current_brush_label
    current_brush_label = label
    current_brush = brushes[label]

def set_selected_block(block):
    global selected_block
    selected_block = block

# --- Adding btns ---
base_btn_all = []
start_y = 30
btn_height = 30

buttons_config = [
    {
        "default_label": "Pause",
        "action": pause_game,
    },
    {
        "default_label": "Reset",
        "action": Reset,
    },
    {
        "default_label": "Dark mode",
        "action": toggle_theme,
    },
    {
        "default_label": "Grid",
        "action": toggle_grid,
    },
]

for index , btn_data in enumerate(buttons_config):
    if index % 2 != 0:
        btn_rect = pygame.Rect(overlay_size/2, start_y, overlay_size/2, btn_height)
        start_y += btn_height
    else:
        btn_rect = pygame.Rect(0, start_y, overlay_size/2, btn_height)

    btn = Base_button(rect=btn_rect,action=btn_data["action"],label = btn_data["default_label"],toggled=False,group=Radiogroup(btn_data["default_label"]))
    base_btn_all.append(btn)


#  BRUSH BUTTONS
brush_group = Radiogroup("brush_group")

columns = 5
cell_width = overlay_size / columns

x = 0
start_y += btn_height

for brush_name in brushes.keys():

    btn = Base_button(
        rect= pygame.Rect(x, start_y, cell_width, btn_height),
        action= lambda b=brush_name: set_brush(b),
        label= brush_name,
        text_color= current_theme["text"],
        bg_color= current_theme["bg"],
        toggled= (current_brush_label == brush_name),
        group= brush_group
    )

    base_btn_all.append(btn)

    # Move to next column
    x += cell_width
    if x >= overlay_size:
        x = 0
        start_y += btn_height


# BLOCK BUTTONS
block_group = Radiogroup("block_group")

columns = 3
cell_width = overlay_size / columns

x = 0
start_y += btn_height

for block_id in blocks.keys():

    rect = pygame.Rect(x, start_y, cell_width, btn_height)

    btn = Base_button(
        rect=rect,
        action= lambda b=block_id: set_selected_block(b),
        label= blocks[block_id]["name"].capitalize(),
        text_color= current_theme["text"],
        bg_color= blocks[block_id]["color"],
        toggled= (selected_block == block_id),
        group= block_group
    )

    base_btn_all.append(btn)

    x += cell_width
    if x >= overlay_size:
        x = 0
        start_y += btn_height


# --- Small helpers ---
def get_reduced_color(color):
    shift = -30 if current_theme == night_theme else 100

    r = max(0, min(255, color[0] + shift))
    g = max(0, min(255, color[1] + shift))
    b = max(0, min(255, color[2] + shift))

    return (r, g, b)

get_close_color = lambda block : random.choice(palette[block])

calculate_padding = lambda lines ,font_size=16 : (font_size + font_size/3) * lines

def logs_add(log):
    if not logs or logs[-1] != log:
        logs.append(log)
    del logs[:-3]

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

def draw_text(text, x, y, color=None ):
    if color is None:
        color = current_theme['text']
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_grid_lines():
    for x in range(grid_rect.left, screen_width + 1, block_size):
        pygame.draw.line(screen, current_theme['fg'], (x, 0), (x, screen_height))
        
    for y in range(0, screen_height + 1, block_size):
        pygame.draw.line(screen, current_theme['fg'], (grid_rect.left, y), (screen_width, y))

def draw_brush():
    for mx, my in current_brush:
        x = overlay_size + (grid_x + mx) * block_size
        y = (grid_y + my) * block_size
        brush_rect = pygame.Rect(x , y , block_size, block_size)
        pygame.draw.rect( screen, current_theme['text'], brush_rect, 1)


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

    for dx, dy in current_brush:
        # chance to not add
        if random.randint(0, 1): continue
        
        # add neighbour
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
    pygame.draw.rect(screen, grid_color[x, y] , pygame.Rect(screen_x, screen_y, block_size, block_size))

    # draw highlight if in debug mode
    if draw_grid:
        color = current_theme['danger' if grid_active[x,y] else 'success']
        pygame.draw.rect(screen, color, pygame.Rect(screen_x, screen_y, block_size, block_size),1)

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
    pygame.draw.rect(screen, current_theme["bg"], grid_rect)

    # grid button
    if draw_grid:
        draw_grid_lines()
        draw_brush()

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
                if game_paused:
                    mark_in_active_grid(x,y)
                else:
                    simulation_block(x, y)
    
# left 
def overlay():
    pygame.draw.rect(screen, current_theme["bg"], overlay_rect)
    pygame.draw.line(screen, current_theme['fg'], [overlay_size, 0], [overlay_size, screen_height],3)

    draw_text(f'FPS {int(mainclock.get_fps())}', 8, screen_height - 72)   
    draw_text(f"X {mouse_x:03d} Y {mouse_y:03d}", 8, screen_height - 48)
    draw_text(f"Cells {np.count_nonzero(grid_active):05d} / {np.count_nonzero(grid_value):05d}", 8, screen_height - 24) 



# main loop
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
                logs_add(f"Selected {blocks[selected_block]['name']}")

            if event.key in [pygame.K_SPACE,pygame.K_RETURN]:
                game_paused = not game_paused
    
    # --- Main partation ---
    game()
    overlay()

    # --- active blocks update ---
    grid_active[:] = grid_active_next
    grid_active_next.fill(False)

    # --- Button ---
    for btn in base_btn_all:
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