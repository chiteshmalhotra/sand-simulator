import pygame as pygame
import numpy as np
import random

# --- Initilize pygame ---

pygame.init()
mainclock = pygame.time.Clock()
pygame.display.set_caption("Sand Simulator 3000")

# --- Screen variables ---

screen_height = 600
screen_width = 800
screen = pygame.display.set_mode((screen_width, screen_height)) 

# --- Logic variables ---

block_size = 5
chunk_size = 10

# overlay
overlay_h = 50
overlay_rect = pygame.Rect(0, 0, screen_width, overlay_h)

# grid
grid_h = (screen_height - overlay_h) // block_size
grid_w  = screen_width // block_size
grid_rect = pygame.Rect( 0, overlay_h, screen_width, screen_height - overlay_h)

grid_value = np.zeros((grid_w, grid_h), dtype=np.uint8)
grid_color = np.zeros((grid_w, grid_h, 3), dtype=np.uint8)

grid_active = np.zeros((grid_w, grid_h), dtype=bool)
grid_active_next = np.zeros((grid_w, grid_h), dtype=bool)

# chunk 
chunk_w = grid_w // chunk_size
chunk_h = grid_h // chunk_size
chunk_active = np.zeros((chunk_w, chunk_h), dtype=bool)
chunk_active_next = np.zeros((chunk_w, chunk_h), dtype=bool)

# --- Color variables ---

theme_text   = (0, 0, 0)
theme_muted   = (150,150,150)
theme_fg  = (197, 197, 197)
theme_bg   = (255, 255, 255)
theme_success = (166, 209, 137)
theme_danger  = (226, 117, 117)

# --- Game variables ---

run = True
direction = True
font = pygame.font.SysFont(None, 24)
immediate_neighbour = [(-1, -1), (0, -1), (1, -1),(-1,  0),(0,0), (1,  0), (-1,  1), (0,  1), (1,  1)]

# --- user variable ---

mouse_x = 0
mouse_y = 0

grid_x = 0 
grid_y = 0

selected_block = 1

debug_mode = False
game_paused = False
mouser_pressed = False
hovering_button = False

tooltip_text = None

# --- Block data ---

blocks = {
    0: { "name": "Void",  "color": (255, 255, 255), "moves": [],
        "density": 0, "state": "solid", "ability": None},
    1: { "name": "sand",  "color": (194, 178, 128), "moves": ["down", "down_diag"],
        "density": 4, "state": "grain", "ability": None},
    2: { "name": "stone", "color": (110, 110, 110), "moves": [],
        "density": 6, "state": "solid", "ability": None},
    3: { "name": "water", "color": (64, 164, 223), "moves": ["down", "down_diag", "side"],
        "density": 2, "state": "liquid", "ability": None},
    4: { "name": "acid",  "color": (57, 255, 20), "moves": ["down", "down_diag", "side", "up"],
        "density": 9, "state": "liquid", "ability": "destroy"},
    5: { "name": "steam", "color": (220, 220, 220), "moves": ["up", "up_diag", "side"],
        "density": 0, "state": "gas", "ability": None}}

moves_dict = {
    "down": [(0, 1)],
    "down_diag": [(-1, 1), (1, 1)],
    "up": [(0, -1)],
    "up_diag": [(-1, -1), (1, -1)],
    "side": [(-1, 0), (1, 0)]
}

# --- Initilize Brush ---

create_brush = lambda r : [(x,y) for x in range(-r, r+1) for y in range(-r, r+1) if x*x + y*y <= r*r]
brushes = {'S': create_brush(2), 'M': create_brush(4), 'L': create_brush(6)}
selected_brush = 'S'

# --- Block palette ---

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

# --- Btn actions ---

def pause_game():
    global game_paused
    game_paused = not game_paused
    chunk_active.fill(True)

def toggle_debug():
    global debug_mode
    debug_mode = not debug_mode
    chunk_active.fill(True)

def Reset():
    grid_value.fill(0)
    grid_color.fill(0)
    screen.fill(theme_bg)

def set_brush(index):
    global selected_brush
    selected_brush = index

def set_selected_block(block_id):
    global selected_block
    selected_block = block_id

# --- Adding btns ---

button_list = []

h = 24
x = 4
y = overlay_h // 2 - h // 2
section_padding = 30

#  main btns
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

x += section_padding

# block selector btns
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
    x += h - 4

x += section_padding

# brush selector btns
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
    x += h - 4

# --- Functions ---

get_close_color = lambda block : random.choice(block_palette[block])

def update_grid_cords(x = mouse_x, y = mouse_y):
    global grid_x, grid_y

    if y < overlay_h:
        return grid_x, grid_y

    temp_grid_x = x // block_size
    temp_grid_y = (y - overlay_h) // block_size

    if 0 <= temp_grid_x < grid_w and 0 <= temp_grid_y < grid_h:
        grid_x, grid_y = temp_grid_x, temp_grid_y

# --- Simulation ---

def activate_neighbors(x, y, neighbours_offset = immediate_neighbour):
    for dx, dy in neighbours_offset:
        # activate neighbour blocks 
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_w and 0 <= my < grid_h:
            if grid_value[mx, my]:
                grid_active_next[mx, my] = True

        # activate neighbour Chunks
        chunk_x, chunk_y = x // chunk_size + dx, y // chunk_size + dy
        if 0 <= chunk_x < chunk_w and 0 <= chunk_y < chunk_h:
            chunk_active_next[chunk_x, chunk_y] = True


def place_block(x, y):
    # place center
    if not grid_value[grid_x, grid_y] or not selected_block:
        grid_value[grid_x, grid_y] = selected_block
        grid_color[grid_x, grid_y] = get_close_color(selected_block)

    # place brush
    for dx, dy in brushes[selected_brush]:
        if random.random() < 0.2: continue
        
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_w and 0 <= my < grid_h:
            if not grid_value[mx, my] or not selected_block:
                grid_value[mx, my] = selected_block
                grid_color[mx, my] = get_close_color(selected_block)
                activate_neighbors(mx,my)


def draw_block(x, y):
    if grid_value[x, y]:
        rect = pygame.Rect(x * block_size , overlay_h + y * block_size, block_size, block_size)
        width = 1 if debug_mode and grid_active[x, y] else 0
        pygame.draw.rect(screen, grid_color[x, y], rect, width)        

    
def move_swap(x, y, x1, y1):  
    grid_value[x, y], grid_value[x1, y1] = grid_value[x1, y1], grid_value[x, y]
    grid_color[x, y], grid_color[x1, y1] = grid_color[x1, y1].copy(), grid_color[x, y].copy()

    activate_neighbors(x, y)
    activate_neighbors(x1, y1)

def move_destroy(x, y, x1, y1):
    grid_value[x1, y1] = 0
    grid_color[x1, y1] = (0,0,0)

    grid_value[x, y] = 0
    grid_color[x, y] = (0,0,0)

    activate_neighbors(x, y)
    activate_neighbors(x1, y1)

def move(x, y, dx=0, dy=0):
    mx, my = x + dx, y + dy

    if not (0 <= mx < grid_w and 0 <= my < grid_h):
        return False

    target_val = grid_value[mx, my]
    current_val = grid_value[x, y]

    # if empty
    if not target_val:
        move_swap(x, y, mx, my)
        return True

    # if not empty
    target_density = blocks[target_val]['density']
    current_denser = blocks[current_val]['density']
    if current_denser > target_density:
        # destroy if capable
        if blocks[current_val]['ability'] == 'destroy':
            move_destroy(x, y, mx, my)
            return True

        # Density move_swap (sand move_swaps water)
        move_swap(x, y, mx, my)
        return True

    return False

def simulate_block(x, y):
    global direction

    if not grid_active[x, y]:
        return

    for move_type in blocks[grid_value[x, y]]["moves"]:
        moves = moves_dict[move_type]
        order = moves if direction else moves[::-1]

        for dx, dy in order:
            if move(x, y, dx, dy):
                return

def simulation():
    for gy in range(chunk_h - 1, -1, -1):
        for gx in range(chunk_w):

            # Compute chunk bounds
            x_start = gx * chunk_size
            x_end   = (gx + 1) * chunk_size
            y_start = gy * chunk_size
            y_end   = (gy + 1) * chunk_size

            chunk_rect = pygame.Rect(x_start * block_size, overlay_h + y_start * block_size, chunk_size * block_size, chunk_size * block_size)

            # Skip inactive chunks           
            if not chunk_active[gx, gy]:
                if debug_mode:
                    pygame.draw.rect(screen, theme_fg, chunk_rect,1)
                continue

            pygame.draw.rect(screen, theme_bg, chunk_rect)
            if debug_mode:
                pygame.draw.rect(screen, theme_danger, chunk_rect,1)

            # Bottom to Top
            for y in range(y_end - 1, y_start - 1, -1):

                # Randomize horizontal scan to prevent bias
                x_range = list(range(x_start, x_end))
                if random.random() < 0.5: x_range.reverse()

                for x in x_range:
                    if grid_value[x, y]:
                        if chunk_active[gx, gy]:
                            draw_block(x, y)

                        if not game_paused:
                            simulate_block(x, y)

# --- Main loop ---
screen.fill(theme_bg)
while run:   
    # --- Variables ---
    tooltip_text = None
    mouse_clicked = False
    direction = not direction
    fps = int(mainclock.get_fps())
    
    # --- Event handling ---
    for event in pygame.event.get():
        
        for btn in button_list:
            btn.handle_event(event)
        
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            update_grid_cords(mouse_x, mouse_y)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouser_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            mouser_pressed = False 
    
    # --- Placement ---
    if grid_rect.collidepoint(mouse_x, mouse_y) and mouser_pressed:
        if 0 <= grid_x < grid_w and 0 <= grid_y < grid_h:           
            place_block(grid_x,grid_y)

    # --- simulate ---
    simulation()

    # --- Overlay UI ---
    pygame.draw.rect(screen, theme_fg, overlay_rect)
    pygame.draw.line(screen, theme_text, (0, overlay_h), (screen_width, overlay_h))

    # --- Debug UI ---
    if debug_mode:
        debug_text = f"FPS {fps} AC {np.count_nonzero(chunk_active):03d} AB {np.count_nonzero(grid_active):04d}"
        text_surface = font.render(debug_text, True, theme_text)
        screen.blit(text_surface, (screen_width - text_surface.get_width() - 10 , (overlay_h - text_surface.get_height()) // 2))

    # --- Update active blocks & chunks for next frame ---
    if not game_paused:
        grid_active[:] = grid_active_next
        grid_active_next.fill(False)

        chunk_active[:] = chunk_active_next
        chunk_active_next.fill(False)

    # --- Buttons ---
    hovering_button = False
    for btn in button_list:
        btn.handle_draw()
        if btn.handle_hover(): 
            hovering_button = True
            if btn.tooltip_text:
                tooltip_text = btn.tooltip_text

    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hovering_button else pygame.SYSTEM_CURSOR_ARROW)

    # --- Tooltips ---
    if tooltip_text:
        tooltip_rect = pygame.Rect(mouse_x + 16, 20, font.size(tooltip_text)[0] + 24, font.size(tooltip_text)[1] + 8)
        pygame.draw.rect(screen, theme_text, tooltip_rect, border_radius=6)
        screen.blit(font.render(tooltip_text, True, theme_bg), tooltip_rect.topleft + pygame.Vector2(12,4))

    # --- Update screen ---
    pygame.display.update()
    mainclock.tick(60)