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
pink = pygame.Color("#e07a9b")
peach = pygame.Color('#ef9f76')
yellow = pygame.Color('#e5c890')
green = pygame.Color('#a6d189')
teal = pygame.Color('#81c8be')
frost = pygame.Color('#85c1dc')
blue = pygame.Color('#8caaee')
purple = pygame.Color('#ca9ee6')

black = pygame.Color("#000000")
grey = pygame.Color('#505050')
muted = pygame.Color('#b4b4b4')
white = pygame.Color('#f0f0f0')

# --- theme variables ---
night_theme = {'bg': black,'fg': grey, 'muted': muted, 'text': white, 'success': green,'danger':pink}
light_theme = {'bg': white, 'fg': muted, 'muted': grey, 'text': black, 'success': green,'danger':pink}

# --- game variables ---
run = True
direction = True
block_size = 5

overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)

grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
grid_rect = pygame.Rect(overlay_size,0,screen_width - overlay_size,screen_height)

grid_value  = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

text_p = pygame.font.SysFont('Arial', 16, bold=True)

neighbors_offset = [
    (-1, -1), (0, -1), (1, -1), 
    (-1,  0), (0,  0), (1,  0), 
    (-1,  1), (0,  1), (1,  1)
]

def make_brush(radius):
    return [(x, y)
            for x in range(-radius, radius + 1)
            for y in range(-radius, radius + 1)
            if x*x + y*y <= radius*radius]

brushes = {
    "XS": make_brush(0),
    "S": make_brush(1),
    "M": make_brush(2),
    "L": make_brush(3),
    "XL": make_brush(4),
}

# --- user variable ---

game_paused = False
debug_mode = False
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

current_brush_label = "M"
current_brush = brushes[current_brush_label]


# --- blocks ---
blocks = {
    1: {
        "name": "sand",
        "color": yellow,
        "density": 4,
        "state": "grain",
        "ability": None,
    },

    2: {
        "name": "stone",
        "color": grey,
        "density": 6,
        "state": "solid",
        "ability": None,
    },

    3: {
        "name": "water",
        "color": blue,
        "density": 2,
        "state": "liquid",
        "ability": None,
    },

    4: {
        "name": "acid",
        "color": teal,
        "density": 9,
        "state": "liquid",
        "ability": "destroy",
    },

    5: {
        "name": "steam",
        "color": purple,
        "density": 0,
        "state": "gas",
        "ability": None,
    },
}


# --- palette ---
def initilize_palette(delta = 8,count = 8):
    complete_palette={}
    for block in blocks.keys():
        r, g, b, alpha = blocks[block]['color']

        single_block_palette = []
        for _ in range(count):
            single_block_palette.append((
                max(0, min(255, r + random.randint(-delta, delta))),
                max(0, min(255, g + random.randint(-delta, delta))),
                max(0, min(255, b + random.randint(-delta, delta))),
                alpha
            ))
        complete_palette[block] = single_block_palette
    return complete_palette

palette = initilize_palette()


# --- btn class ---
class Button:
    def __init__(self, rect, default_label, alt_label, click_action=None):
        self.rect = rect

        self.default_label = default_label
        self.alt_label = alt_label
        self.text = default_label

        self.click_action = click_action

        self.bg_color = current_theme["bg"]
        self.text_color = current_theme["text"]

        self.font = pygame.font.SysFont(None, 24)

        self.isactive = False
        self.ishovered = False

    def draw(self, surface):
        self.bg_color = current_theme["text" if self.ishovered else "bg"]
        self.text_color = current_theme["bg" if self.ishovered else "text"]
        self.text = self.alt_label if self.isactive else self.default_label

        pygame.draw.rect(surface, self.bg_color, self.rect,)
        pygame.draw.rect(surface, current_theme["fg"], self.rect, 1)

        text = self.font.render(self.text, True, self.text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def update(self):
        if self.rect.collidepoint((mouse_x, mouse_y)):
            self.ishovered = True
            logs_add(f'{self.text} btn hovered')
            return True
        else:
            self.ishovered = False
            return False

    def handle_event(self, event):
        if self.rect.collidepoint(mouse_x, mouse_y):
            logs_add(f'{self.text} btn clicked')
            self.isactive = not self.isactive
            if self.click_action:
                self.click_action()

class Radiogroup:
    def __init__(self, groupname):
        self.groupname = groupname
        self.radios = []

    def add(self, radio):
        self.radios.append(radio)

    def select(self, selected_radio):
        for radio in self.radios:
            radio.istoggled = False
        selected_radio.istoggled = True

class Radio():
    def __init__(self, rect, group: Radiogroup,
                 click_action=None,
                 label='',
                 toggled=False,
                 color=None):

        self.rect = rect
        self.group = group
        group.add(self)

        self.istoggled = toggled
        self.ishovered = False
        self.click_action = click_action
        self.label = label
        self.custom_color = color
        self.font = pygame.font.SysFont(None, 22)

    def draw(self, surface):

        # --- Base background ---
        if self.custom_color is not None:
            bg_color = self.custom_color
        else:
            bg_color = current_theme["bg"]

        # --- Hover effect (subtle brightness) ---
        if self.ishovered and not self.istoggled:
            bg_color = (
                min(255, bg_color[0] + 20),
                min(255, bg_color[1] + 20),
                min(255, bg_color[2] + 20)
            )

        pygame.draw.rect(surface, bg_color, self.rect)

        # --- Toggled highlight ---
        if self.istoggled:
            pygame.draw.rect(surface, current_theme["text"], self.rect, 3)
            border_width = 3
            border_color = current_theme["text"]
        else:
            pygame.draw.rect(surface, current_theme["fg"], self.rect, 1)

        # --- Label ---
        if self.label:
            text_color = current_theme["text"]
            label_surface = self.font.render(self.label, True, text_color)
            surface.blit(label_surface, label_surface.get_rect(center=self.rect.center))

    def update(self):
        self.ishovered = self.rect.collidepoint(mouse_x, mouse_y)
        return self.ishovered

    def handle_event(self):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.ishovered:
                self.group.select(self)
                if self.click_action:
                    self.click_action()

# --- btn funstions ---
def pause_game():
    global game_paused
    game_paused = not game_paused

def toggle_theme():
    global current_theme
    current_theme = light_theme if current_theme == night_theme else night_theme

def debug_mode():
    global debug_mode
    debug_mode = not debug_mode

def Reset():
    global grid_value,grid_color
    grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
    grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)

def set_brush(label):
    global current_brush, current_brush_label
    current_brush_label = label
    current_brush = brushes[label]

def set_selected_block(block):
    global selected_block
    selected_block = block

# --- Adding btns ---
btns = []
start_y = 30
btn_height = 30

buttons_config = [
    {
        "default_label": "Pause",
        "alt_label": "Run",
        "click_action": pause_game,
    },
    {
        "default_label": "Reset",
        "alt_label": "Reset",
        "click_action": Reset,
    },
    {
        "default_label": "Night",
        "alt_label": "Light",
        "click_action": toggle_theme,
    },
    {
        "default_label": "Debug",
        "alt_label": "Normal",
        "click_action": debug_mode,
    },
]

for index , btn_data in enumerate(buttons_config):
    if index % 2 != 0:
        btn_rect = pygame.Rect(overlay_size/2, start_y, overlay_size/2, btn_height)
        start_y += btn_height
    else:
        btn_rect = pygame.Rect(0, start_y, overlay_size/2, btn_height)

    btn = Button( rect= btn_rect, default_label= btn_data["default_label"],alt_label= btn_data["alt_label"],click_action= btn_data["click_action"])
    btns.append(btn)


# --- Adding btns ---
radio_all = []
brush_group = Radiogroup("brush_group")

x = 0
start_y += btn_height

for label, brush in brushes.items():
    btn_rect = pygame.Rect(x, start_y, overlay_size/5, btn_height)

    click_action = lambda l=label: set_brush(l)

    btn = Radio(
        btn_rect,
        brush_group,
        click_action,
        label=label,
        toggled=(current_brush_label == label)
    )

    radio_all.append(btn)
    x += overlay_size / 5


x = 0
start_y += btn_height *2
block_group = Radiogroup("block_group")
for index ,block  in enumerate(blocks.keys()):
    btn_rect = pygame.Rect(x, start_y, overlay_size/5, btn_height)    
    click_action = lambda block = block: set_selected_block(block)
    btn = Radio( 
        btn_rect, 
        block_group, 
        click_action,
        color = blocks[block]['color'],
        toggled=(selected_block == index))
    radio_all.append(btn)
    x += overlay_size/5

# --- Small helpers ---
get_darker_color = lambda color : (color[0]-60, color[1]-60, color[2]-60)

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
    text_surface = text_p.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_demo(x, y, color=None, size=15, border_width=2, border_radius=20):
    if color is None:
        color = current_theme['text']

    rect = pygame.Rect(x, y, size, size)

    # Fill
    pygame.draw.rect(screen, color, rect, border_radius=border_radius)
    pygame.draw.rect(screen, current_theme['text'], rect, border_width, border_radius)

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
    grid_value[x1, y1] = grid_value[x, y]
    grid_color[x1, y1] = grid_color[x, y].copy()

    grid_value[x, y] = 0
    grid_color[x, y] = (0,0,0,0)

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

def add_brush_block(x, y):
    grid_value[grid_x, grid_y] = selected_block
    grid_color[grid_x, grid_y] = get_close_color(selected_block)
    mark_in_active_grid(grid_x,grid_y)
    logs_add(f'Added {blocks[grid_value[x, y]]['name']} at x {grid_x} y {grid_y}')

    for dx, dy in current_brush:
        # chance to not add
        if random.randint(0, 1): continue
        
        # add neighbour
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            mark_in_active_grid(mx,my)
            neighbors_color = get_close_color(selected_block) if selected_block else blocks[selected_block]["color"]
            grid_value[mx, my] = selected_block
            grid_color[mx, my] = neighbors_color
            logs_add(f'Added {blocks[grid_value[x, y]]['name']} at x {mx} y {my}')

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
    if debug_mode:
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
    if debug_mode:
        draw_grid_lines()
        draw_brush()

    # Placement logic
    if grid_rect.collidepoint(mouse_x, mouse_y) and mouser_pressed:
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:           
            add_brush_block(grid_x,grid_y)

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
    # bg and Border
    pygame.draw.rect(screen, current_theme["bg"], overlay_rect)
    pygame.draw.line(screen, current_theme['text'], [overlay_size, 0], [overlay_size, screen_height])

    lines = 16

    # --- debug mode ---
    if debug_mode:
        current_fps = f'FPS {int(mainclock.get_fps())}'
        draw_text(current_fps, 8, calculate_padding(lines))   

        lines += 1
        draw_demo(120, calculate_padding(lines), blocks[selected_block]['color'])
        draw_text( f'Selected {blocks[selected_block]['name'].capitalize()}', 8, calculate_padding(lines)) 

        lines += 1
        draw_text(f"Alive {np.count_nonzero(grid_active):05d} / {np.count_nonzero(grid_value):05d}", 8, calculate_padding(lines)) 

        lines += 1
        draw_text(f"Grid       X {grid_x+1:03d} Y {grid_y+1:03d}", 8, calculate_padding(lines))
        lines += 1
        draw_text(f"Mouse  X {mouse_x:03d} Y {mouse_y:03d}", 8, calculate_padding(lines))

        lines += 2
        draw_text("Subtitles", 8, calculate_padding(lines))
        for log in logs[::-1]:
            lines += 1
            draw_text(log , 8, calculate_padding(lines))



# main loop
while run:   
    # --- event loop ---
    for event in pygame.event.get():
        # quit
        if event.type == pygame.QUIT:
            run = False

        # mouse key pressed
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_clicked = True
            mouser_pressed = True

        elif event.type == pygame.MOUSEBUTTONUP:
            mouser_pressed = False

        # keyboard shorcuts
        elif event.type == pygame.KEYDOWN:

            # select block
            key_num = event.key - pygame.K_0
            if key_num in blocks:
                selected_block = key_num
                logs_add(f"Selected {blocks[selected_block]['name']}")

            # pause game
            if event.key in [pygame.K_SPACE,pygame.K_RETURN]:
                game_paused = not game_paused
    
    # --- Main partation ---
    game()
    overlay()

    # --- active blocks update ---
    grid_active[:] = grid_active_next
    grid_active_next.fill(False)

    # --- Button ---
    for btn in btns:
        btn.draw(screen)
        if overlay_rect.collidepoint(mouse_x, mouse_y):
            if mouse_clicked:
                btn.handle_event(event)

            if btn.update():
                hovering_button = True

    for btn in radio_all:
        btn.draw(screen)
        if overlay_rect.collidepoint(mouse_x, mouse_y):
            if mouse_clicked:
                btn.handle_event()

            if btn.update():
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