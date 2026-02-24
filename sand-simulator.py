import pygame as pygame
import numpy as np
import random

pygame.init()
mainclock = pygame.time.Clock()

# --- display variables ---
screen_size= 700
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
dark_theme = {'bg': black,'fg': grey, 'muted': muted, 'text': white, 'success': green,'danger':pink}
light_theme = {'bg': white, 'fg': muted, 'muted': grey, 'text': black, 'success': green,'danger':pink}

# --- game variables ---
run = True
direction = True
block_size = int(screen_size/100)

grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
grid_rect = pygame.Rect(overlay_size,0,screen_width - overlay_size,screen_height)

grid_value  = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

text_p = pygame.font.SysFont('Arial', 16)
text_bold = pygame.font.SysFont('Arial', 16, bold=True)
neighbors_offset = [
    (-1, -1), (0, -1), (1, -1), 
    (-1,  0), (0,  0), (1,  0), 
    (-1,  1), (0,  1), (1,  1)
]

# --- user variable ---
grid_x = 0 
grid_y = 0

mouse_x = 0
mouse_y = 0

hovered_block = 0
selected_block = 1

mouse_pressed = False

logs = ["No logs yet"]
current_theme = dark_theme
current_brush = [(x, y) for x in range(-1, 2) for y in range(-1, 2)]

# --- btn variable ---
blocks = {
    0: {
        "name": "air",
        "color": black,
        "density": 0,
        "state": None,
        "ability": None,
    },

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
        "color": pink,
        "density": 0,
        "state": "gas",
        "ability": None,
    },
}

buttons = {
    "pause_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Pause game",
        "group": None,
        "value": None,
    },

    "clear_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Clear screen",
        "group": None,
        "value": None,
    },

    "debug_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Debug Mode",
        "group": None,
        "value": None,
    },

    "dark_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Dark Mode",
        "group": None,
        "value": None,
    },

    "brush_sm_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Brush sm",
        "group": "brush",
        "value": [(0, -1), (0, 1), (0, 0), (-1,  0), (1,  0)],
    },

    "brush_md_btn": {
        "clicked": True,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Brush md",
        "group": "brush",
        "value": [(x, y) for x in range(-1, 2) for y in range(-1, 2)],
    },

    "brush_lg_btn": {
        "clicked": False,
        "rect": pygame.Rect(0, 0, 16, 16),
        "display": True,
        "label": "Brush lg",
        "group": "brush",
        "value": [(x, y) for x in range(-2, 3) for y in range(-2, 3)],
    },
}

# adds all block btn 
for key, block in blocks.items():
    buttons[f'block_{key}_btn'] = {
        "clicked": False,
        "display": False,
        "label": key,
        "group": "select",
        "value": key,
        "rect": pygame.Rect(0, 0, 0, 0)
    }

# generate palette
delta = 8
count = 8
palette = {}
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
    palette[block] = single_block_palette

# --- Small helpers ---

get_close_color = lambda block : random.choice(palette[block])

calculate_padding = lambda lines ,font_size=16 : (font_size + font_size/3) * lines

def logs_add(log):
    if not logs or logs[-1] != log:
        logs.append(log)
    del logs[:-2]

def get_grid_cords():
    global grid_x, grid_y
    
    adjusted_x = mouse_x - overlay_size
    
    temp_grid_x = int(adjusted_x / block_size)
    temp_grid_y = int(mouse_y / block_size)

    if 0 <= temp_grid_x < grid_width and  0 <= temp_grid_y < grid_height:
        grid_x = temp_grid_x
        grid_y = temp_grid_y
    
    return grid_x, grid_y

# --- Button ---

def draw_all_button(color=None,radius = 7):
    for btn in buttons.values():
        if btn['display']:
            center = (btn['rect'].x + radius, btn['rect'].y + radius)
            if color is None: 
                color = current_theme['text']

            if btn['clicked']:
                pygame.draw.circle(screen, color, center, radius - 4)
            pygame.draw.circle(screen, current_theme["text"], center, radius, 2)

def hover_all_button():
    for btnname,btn in buttons.items():
        rect = btn['rect']
        if rect.collidepoint(mouse_x, mouse_y):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            logs_add(f'Hovered on {btnname}')
            return

    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

def active_all_buttons():
    for btn in buttons.values():
        rect = btn['rect']

        if rect.collidepoint(mouse_x, mouse_y):
            btn['clicked'] = not btn['clicked']
            logs_add(f"clicked {btn['label']}")
            return           

def effect_all_buttons():
    global grid_value,grid_color,selected_block,current_brush,current_theme
    for btn in buttons.values():
        # brush group
        if btn.get("group") == "brush" and btn["clicked"]:
            current_brush = btn["value"]
            btn["clicked"] = False

        # select group
        if btn.get("group") == "select" and btn["clicked"]:
            selected_block = btn["value"]  
            btn["clicked"] = False   

    # clear screen
    if buttons["clear_btn"]["clicked"]:
        grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
        grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
        buttons["clear_btn"]["clicked"] = False
    
    # dark theme 
    current_theme = dark_theme if buttons["dark_btn"]["clicked"] else light_theme

    # debug mode
    if buttons['debug_btn']['clicked']:
        draw_brush()

# --- Draw helpers ---

def draw_text(text, x, y, color=None, bold=False ):
    if color is None:
        color = current_theme['text' if bold else 'muted']
    text_surface = text_bold.render(text, True, color) if bold else text_p.render(text, True, color)
    screen.blit(text_surface, (x, y))
    
def draw_demo(x, y, color=None,width=0,border_radius = 2):    
    if color is None:
        color = current_theme['muted']
    pygame.draw.rect(screen, color, pygame.Rect(x, y, 14, 14), width, border_radius)

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
    grid_color[x, y] = blocks[0]['color']

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
    logs_add(f'Added block at x {grid_x} y {grid_y}')

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
            logs_add(f'Added block at x {mx} y {my}')

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
    if buttons['debug_btn']['clicked']:
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
    if buttons["debug_btn"]["clicked"]:
        draw_grid_lines()

    # Placement logic
    if grid_rect.collidepoint(mouse_x, mouse_y) and mouse_pressed:
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
                if buttons["pause_btn"]["clicked"]:
                    mark_in_active_grid(x,y)
                else:
                    simulation_block(x, y)
    
# left 
def overlay():
    # bg and Border
    overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)
    pygame.draw.rect(screen, current_theme["bg"], overlay_rect)

    pygame.draw.line(screen, current_theme['text'], [overlay_size, 0], [overlay_size, screen_height])
    draw_all_button()

    lines = 0

    # --- selected ---
    lines += 1
    draw_text("Selected", 8, calculate_padding(lines),bold=True)
    lines += 1
    draw_demo(8, calculate_padding(lines), blocks[selected_block]['color'])
    draw_text(blocks[selected_block]['name'].capitalize(), 32, calculate_padding(lines))    

    # --- Buttons ---
    lines += 2
    draw_text('Actions', 8, calculate_padding(lines),bold=True)
    for btn in buttons.values():
        if btn['display']:
            lines += 1
            draw_text(str(btn["label"]), 32, calculate_padding(lines))
            btn['rect'] = pygame.Rect(8 ,calculate_padding(lines),overlay_size - 16,16)
    
    # --- shortcuts ---
    lines += 1
    for key, block in blocks.items():
        lines += 1
        y = calculate_padding(lines)

        draw_demo(8, y, block['color'])
        draw_text(f"{key}   {block['name'].capitalize()}", 32, y)

        buttons[f'block_{key}_btn']["rect"] = pygame.Rect(8, y, overlay_size - 16, 16)

    # --- debug mode ---
    if buttons['debug_btn']['clicked']:
        lines += 2
        draw_text("Statis", 8, calculate_padding(lines),bold=True)

        # fps 
        lines += 1
        current_fps = f'FPS {int(mainclock.get_fps())}'
        draw_text(current_fps, 8, calculate_padding(lines))   

        # active blocks
        lines += 1
        draw_demo(8, calculate_padding(lines), current_theme['danger'] , 2)
        draw_text(f"Alive {np.count_nonzero(grid_active):05d}", 32, calculate_padding(lines))    

        # total blocks
        lines += 1
        draw_demo(8, calculate_padding(lines), current_theme['success'], 2)
        draw_text(f"Total {np.count_nonzero(grid_value):05d}", 32, calculate_padding(lines)) 

        # hovered
        lines += 1
        draw_demo(8, calculate_padding(lines), blocks[hovered_block]['color'])
        draw_text(f"hovered {blocks[hovered_block]['name']}", 32, calculate_padding(lines))
        lines += 1
        draw_text(f"Grid       X {grid_x+1:03d} Y {grid_y+1:03d}", 8, calculate_padding(lines))
        lines += 1
        draw_text(f"Mouse  X {mouse_x:03d} Y {mouse_y:03d}", 8, calculate_padding(lines))

        # Subtitles
        lines += 2
        draw_text("Subtitles", 8, calculate_padding(lines),bold=True)
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
            mouse_pressed = True
            logs_add('Mouse pressed')
            active_all_buttons()

        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_pressed = False

        # keyboard key pressed
        elif event.type == pygame.KEYDOWN:

            # update selected via shorcuts
            key_num = event.key - pygame.K_0
            if key_num in blocks:
                before = selected_block
                selected_block = key_num
                logs_add(f"{blocks[before]['name']} to {blocks[selected_block]['name']}")

            # pause game via shorcuts
            if event.key in [pygame.K_SPACE,pygame.K_RETURN]:
                buttons['pause_btn']['clicked'] = not buttons['pause_btn']['clicked']
    
    # --- Variables ---
    direction = not direction
    hovered_block = grid_value[grid_x, grid_y]
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = get_grid_cords()
    
    # --- Button effect ---
    hover_all_button()
    effect_all_buttons()

    # --- Main partation ---
    game()
    overlay()

    # --- active blocks update ---
    grid_active[:] = grid_active_next
    grid_active_next.fill(False)

    # --- update screen ---
    pygame.display.update()
    mainclock.tick(60)