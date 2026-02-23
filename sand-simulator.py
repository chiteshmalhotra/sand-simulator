import pygame as pygame
import numpy as np
import random

pygame.init()
mainclock = pygame.time.Clock()

# main variables
screen_size= 700
overlay_size = 150

# screen
screen_height = screen_size
screen_width = screen_size + overlay_size
screen = pygame.display.set_mode((screen_width, screen_height)) 

# theme
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

dark_theme = {'bg': black,'lines': green, 'muted': muted, 'text': white, 'debug': green}
light_theme = {'bg': white, 'lines': green, 'muted': grey, 'text': black, 'debug': green}
current_theme = dark_theme

# variables
run = True
direction = True
block_size = int(screen_size/100)

overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)
grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
grid_size = grid_height * grid_width
grid_rect = pygame.Rect(overlay_size,0,screen_width - overlay_size,screen_height)

grid_value  = np.zeros((grid_width, grid_height), dtype=np.uint8)
grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
grid_active = np.zeros((grid_width, grid_height), dtype=bool)
grid_active_next = np.zeros((grid_width, grid_height), dtype=bool)

text_p = pygame.font.SysFont('Arial', 16)
text_bold = pygame.font.SysFont('Arial', 16, bold=True)
small_mouse = [(0, -1), (-1,  0), (1,  0), (0,  1)]
big_mouse = [(2, 0), (0, -2), (-0, 2), (-2, -0)]
neighbors_offset = [(-1, -1), (0, -1), (1, -1), (-1,  0), (1,  0), (-1,  1), (0,  1), (1,  1)]


# user variable
grid_x = 0 
grid_y = 0
mouse_x = 0
mouse_y = 0
selected = 1
hovered = 0
mouse_pressed = False
logs = ["No logs yet"]

blocks = {  0 : {'name': 'air'   , 'color': black  , 'density':0,'state': None, 'ability': None},
            1 : {'name': 'sand'   , 'color': yellow , 'density':4,'state': 'grain', 'ability': None},
            2 : {'name': 'stone'  , 'color': grey   , 'density':6,'state': 'solid', 'ability': None},
            3 : {'name': 'water'  , 'color': blue   , 'density':2,'state': 'liqued', 'ability': None},
            4 : {'name': 'acid'   , 'color': teal   , 'density':9,'state': 'liqued', 'ability': 'destroy'},
            5 : {'name': 'steam'  , 'color': pink   , 'density':0,'state': 'gas', 'ability': None},}

buttons = { "pause_btn": {"state": False, "rect": pygame.Rect(0, 0, 16, 16), "display": True, "label": 'Pause game'},
            "clear_btn": {"state": False, "rect": pygame.Rect(0, 0, 16, 16), "display": True, "label": 'Clear screen'},
            "brush_btn": {"state": False, "rect": pygame.Rect(0, 0, 16, 16), "display": True, "label": 'Brush SM'},
            "dark_btn" : {"state": False, "rect": pygame.Rect(0, 0, 16, 16), "display": True, "label": 'Dark Mode'},
            "debug_btn": {"state": False, "rect": pygame.Rect(0, 0, 16, 16), "display": True, "label": 'Debug Mode'}}

# generate palette
delta = 10
count = 10
palette = {}
for block in blocks.keys():
    r, g, b, a = blocks[block]['color']
    single_palette = []
    for _ in range(count):
        single_palette.append((
            max(0, min(255, r + random.randint(-delta, delta))),
            max(0, min(255, g + random.randint(-delta, delta))),
            max(0, min(255, b + random.randint(-delta, delta))),
            a
        ))
    palette[block]=single_palette


# --- Helpers ---

def calculate_padding (lines,font_size=16):
    return (font_size + font_size/3) * lines

def get_close_color(block):
    return random.choice(palette[block])

def get_grid_cords():
    global grid_x, grid_y
    
    adjusted_x = mouse_x - overlay_size
    
    temp_grid_x = int(adjusted_x / block_size)
    temp_grid_y = int(mouse_y / block_size)

    if 0 <= temp_grid_x < grid_width and  0 <= temp_grid_y < grid_height:
        grid_x = temp_grid_x
        grid_y = temp_grid_y
    
    return grid_x, grid_y

def logs_add(log):
    global logs
    if logs[-1] != log:
        logs.append(log)
    if len(logs)>3:
        logs=logs[-3::]

# --- Button ---

def draw_all_button(color=None,radius = 7):
    for btn in buttons.values():
        if btn['display']:
            center = (btn['rect'].x + radius, btn['rect'].y + radius)
            if color == None: color = current_theme['text']

            if btn['state']:
                pygame.draw.circle(screen, color, center, radius - 4)
            pygame.draw.circle(screen, current_theme["text"], center, radius, 2)

def hover_all_button():
    for btnname,btn in buttons.items():
        rect = btn['rect']
        if rect.collidepoint(mouse_x, mouse_y):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            logs_add(f'Hovered {btnname}')
            return

    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

def active_all_buttons():
    for btn in buttons.values():
        rect = btn['rect']

        if rect.collidepoint(mouse_x, mouse_y):
            btn['state'] = not btn['state']
            logs_add(f"clicked {btn['label']}")
            return           

# --- Draw ---

def draw_text(text, x, y, color=None, bold=False ):
    if color is None:
        color = current_theme['text' if bold else 'muted']
    text_surface = text_bold.render(text, True, color) if bold else text_p.render(text, True, color)
    screen.blit(text_surface, (x, y))
    
def draw_demo_block(x, y, color=None,radius = 2):
    block_rect = pygame.Rect(x, y, 14, 14)
    if color == None: color = current_theme['text']
    pygame.draw.rect(screen, color, block_rect, border_radius=radius)

def draw_grid_lines():
    for x in range(grid_rect.left, screen_width + 1, block_size):
        pygame.draw.line(screen, current_theme['debug'], (x, 0), (x, screen_height))
        
    for y in range(0, screen_height + 1, block_size):
        pygame.draw.line(screen, current_theme['debug'], (grid_rect.left, y), (screen_width, y))

# --- Simulation ---
def is_replacable(x, y,x1,y1):
    before = blocks[grid_value[x,y]]['density']
    after = blocks[grid_value[x1,y1]]['density']
    if before > after :
        return True
    return False

def toggle_in_active_grid(x, y):
    if 0 <= x < grid_width and 0 <= y < grid_height:
        grid_active_next[x, y] = True

    for dx, dy in neighbors_offset:
        mx = x + dx
        my = y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            if grid_value[mx,my]:
                grid_active_next[mx, my] = True

def swap(x, y, x1, y1):  
    grid_value[x, y], grid_value[x1, y1] = \
    grid_value[x1, y1], grid_value[x, y]

    grid_color[x, y], grid_color[x1, y1] = \
    grid_color[x1, y1].copy(), grid_color[x, y].copy()

    toggle_in_active_grid(x, y)
    toggle_in_active_grid(x1, y1)
    
def destroy(x, y, x1, y1):
    grid_value[x1, y1] = grid_value[x, y]
    grid_color[x1, y1] = grid_color[x, y].copy()

    grid_value[x, y] = 0
    grid_color[x, y] = blocks[0]['color']

    toggle_in_active_grid(x, y)
    toggle_in_active_grid(x1, y1)

def move(x, y, dx=0, dy=0):
    mx = x + dx
    my = y + dy

    # out of bounds
    if mx < 0 or mx >= grid_width or my < 0 or my >= grid_height:
        return False

    # Swap if not empty
    if not grid_value[mx, my]:
        swap(x, y, mx, my)
        return True

    # check if is replacable
    if is_replacable(x, y, mx, my):

        # destroy if acid 
        if blocks[grid_value[x, y]]['ability'] == 'destroy':
            destroy(x, y, mx, my)
            return True

        # swap as replacable
        swap(x, y, mx, my)
        return True

    return False

def add_neighbour_block(x, y):
    for dx, dy in neighbors_offset:
        # chance to not add
        if random.randint(0, 1): continue
        
        # add neighbour
        mx, my = x + dx, y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            toggle_in_active_grid(mx,my)
            neighbors_color = get_close_color(selected) if selected else blocks[selected]["color"]
            grid_value[mx, my] = selected
            grid_color[mx, my] = neighbors_color

def draw_all_block(x,y):
    screen_y = block_size * y
    screen_x = overlay_size + block_size * x 

    # block
    pygame.draw.rect(screen, grid_color[x, y], pygame.Rect(screen_x, screen_y, block_size, block_size))

    # draw highlight if in debug mode
    if grid_active[x,y] and buttons['debug_btn']['state']:
        pygame.draw.rect(screen, current_theme['lines'], pygame.Rect(screen_x, screen_y, block_size, block_size),1)

def simulation_block(x,y):
    block = blocks[grid_value[x, y]]['name']

    if not grid_active[x,y]:
        return
    
    # solid
    if block in ['stone']:
        possible_moves = []

    # grainy solid
    if block in ['sand','gravel']:
        if direction:
            possible_moves = (move_down(x, y), move_down_right(x, y), move_down_left(x, y))
        else:
            possible_moves = (move_down(x, y), move_down_left(x, y), move_down_right(x, y))

    # liqued
    if block in ['water','acid']:
        if direction:
            possible_moves = (move_down(x, y), move_down_right(x, y), move_down_left(x, y), move_right(x, y), move_left(x, y))
        else:    
            possible_moves = (move_down(x, y), move_down_left(x, y), move_down_right(x, y), move_left(x, y), move_right(x, y))

    # gas
    if block in ['steam']:
        if direction:
            possible_moves = (move_up(x, y), move_up_right(x, y), move_up_left(x, y), move_right(x, y), move_left(x, y))
        else:
            possible_moves = (move_up(x, y), move_up_left(x, y), move_up_right(x, y), move_left(x, y), move_right(x, y))
    
    for possible_move in possible_moves:
        if possible_move:
            toggle_in_active_grid(x, y)
            return

move_up  = lambda x,y : move(x,y,0,-1)
move_up_left  = lambda x,y : move(x,y,-1,-1)
move_up_right = lambda x,y : move(x,y,1,-1)
move_left  = lambda x,y : move(x,y,-1,0)
move_right = lambda x,y : move(x,y,1,0)
move_down  = lambda x,y : move(x,y,0,1)
move_down_left  = lambda x,y : move(x,y,-1,1)
move_down_right = lambda x,y : move(x,y,1,1)

# right
def game():
    pygame.draw.rect(screen, current_theme["bg"], grid_rect)

    # grid button
    if buttons["debug_btn"]["state"]:
        draw_grid_lines()

    # Placement logic
    if grid_rect.collidepoint(mouse_x, mouse_y)and mouse_pressed:
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid_value[grid_x, grid_y] = selected
            grid_color[grid_x, grid_y] = get_close_color(selected)
            toggle_in_active_grid(grid_x,grid_y)
            
            if not buttons["brush_btn"]["state"]:
                add_neighbour_block(grid_x,grid_y)

    # loop bottom to top
    for y in range(grid_height - 1, -1, -1):
        x_order = list(range(grid_width))
        random.shuffle(x_order)

        for x in x_order:
            if grid_value[x, y]:
                # draw
                draw_all_block(x, y)

                # Simulation
                if buttons["pause_btn"]["state"]:
                    toggle_in_active_grid(x,y)
                else:
                    simulation_block(x, y)
    
# left 
def overlay():
    # bg and Border
    pygame.draw.rect(screen, current_theme["bg"], overlay_rect)

    pygame.draw.line(screen, current_theme['text'], [overlay_size, 0], [overlay_size, screen_height])
    draw_all_button()

    lines = 0

    # --- selected Selection ---
    lines += 1
    draw_text("Selected", 8, calculate_padding(lines),bold=True)
    lines += 1
    draw_demo_block(8, calculate_padding(lines), blocks[selected]['color'])
    draw_text(blocks[selected]['name'].capitalize(), 32, calculate_padding(lines))    

    # --- Buttons ---
    lines += 2
    draw_text('Actions', 8, calculate_padding(lines),bold=True)
    for btn in buttons.values():
        if btn['display']:
            lines += 1
            draw_text(btn["label"], 32, calculate_padding(lines))
            btn['rect'] = pygame.Rect(8 ,calculate_padding(lines),overlay_size - 16,16)
    
    # --- shortcuts ---
    lines += 2
    draw_text('Blocks', 8, calculate_padding(lines),bold=True)
    for key,block in blocks.items():
        lines += 1
        draw_demo_block(8, calculate_padding(lines), block['color'])
        draw_text(f'{block['name'].capitalize()} ({key})', 32, calculate_padding(lines))
        buttons[f'{key}_btn'] = {
            "state": False,
            "rect": pygame.Rect(8, calculate_padding(lines), overlay_size - 16, 16),
            "display": False,
            "label": f'{key}_btn'
        }

    # --- debug mode ---
    if buttons['debug_btn']['state']: # stats
        lines += 2
        draw_text("Debug Menu", 8, calculate_padding(lines),bold=True)

        # fps 
        lines += 1
        current_fps = f'FPS {int(mainclock.get_fps())}'
        draw_text(current_fps, 8, calculate_padding(lines))   

        # active blocks
        lines += 1
        draw_text(f"Alive {np.count_nonzero(grid_active):05d}", 8, calculate_padding(lines))    

        # total blocks
        lines += 1
        draw_text(f"Total {np.count_nonzero(grid_value):05d}", 8, calculate_padding(lines)) 

        # hovered
        lines += 2
        draw_demo_block(8, calculate_padding(lines), blocks[hovered]['color'])
        draw_text(f"{blocks[hovered]['name']}", 32, calculate_padding(lines))
        lines += 1
        draw_text(f"GX {grid_x+1:03d}   GY {grid_y+1:03d}", 8, calculate_padding(lines))
        lines += 1
        draw_text(f"MX {mouse_x:03d}  MY {mouse_y:03d}", 8, calculate_padding(lines))

        # Subtitles
        lines += 2
        draw_text("Subtitles", 8, calculate_padding(lines),bold=True)
        for log in logs[::-1]:
            lines += 1
            draw_text(log , 8, calculate_padding(lines))

# main loop
while run:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = get_grid_cords()
    direction = not direction

    hover_all_button()

    # event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pressed = True
            logs_add('Mouse pressed')
            active_all_buttons()

        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_pressed = False

        elif event.type == pygame.KEYDOWN:
            key_num = event.key - pygame.K_0
            if key_num in blocks:
                before = selected
                selected = key_num
                logs_add(f"{blocks[before]['name']} to {blocks[selected]['name']}")
            if event.key in [pygame.K_SPACE,pygame.K_RETURN]:
                buttons['pause_btn']['state'] = not buttons['pause_btn']['state']


    # hoverred block
    hovered = grid_value[grid_x, grid_y]
    
    # theme change 
    current_theme = dark_theme if buttons["dark_btn"]["state"] else  light_theme

    # clear screen
    if buttons["clear_btn"]["state"]:
        grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
        grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
        buttons["clear_btn"]["state"] = False

    # select block
    for btnname, btn in buttons.items():
        if btn["state"] and btnname.endswith("_btn"):
            try:
                block_id = int(btnname.replace("_btn", ""))
                if block_id in blocks:
                    selected = block_id
            except ValueError:
                pass
        
    # partations
    game()
    overlay()

    grid_active[:] = grid_active_next
    grid_active_next.fill(False)

    # update 
    pygame.display.update()
    mainclock.tick(60)