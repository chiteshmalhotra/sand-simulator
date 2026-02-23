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

dark_theme = {'bg': black,'lines': green, 'muted': muted,'text': white}
light_theme = {'bg': white, 'lines': green, 'muted': grey, 'text': black}
current_theme = dark_theme

# variables
run = True
direction = True
block_size = int(screen_size/100)

overlay_rect = pygame.Rect(0,0,overlay_size,screen_height)
grid_height = int(screen_height / block_size)
grid_width = int((screen_width - overlay_size) / block_size)
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
last_command = "No command yet"

blocks = {  0 : {'name': 'void' , 'color': pink   , 'density':0, 'ability': None},
            1 : {'name': 'sand' , 'color': yellow , 'density':4, 'ability': None},
            2 : {'name': 'stone', 'color': grey   , 'density':6, 'ability': None},
            3 : {'name': 'water', 'color': blue   , 'density':2, 'ability': None},
            4 : {'name': 'acid' , 'color': teal   , 'density':10, 'ability': 'destroy'}}

buttons = { "pause_btn": {"state": False, "cord": [0, 0], "label": 'Pause game'},
            "clear_btn": {"state": False, "cord": [0, 0], "label": 'Clear screen'},
            "brush_btn": {"state": False, "cord": [0, 0], "label": 'Brush SM'},
            "dark_btn" : {"state": False, "cord": [0, 0], "label": 'Dark Mode'},
            "debug_btn": {"state": False, "cord": [0, 0], "label": 'Debug Mode'}}

shorcuts = {}
for num,block in blocks.items():
    shorcuts.update({num:block['name']})

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

# draw helpers
def draw_text(text, x, y, color=None, bold=False ):
    if color is None:
        color = current_theme['text' if bold else 'muted']
    text_surface = text_bold.render(text, True, color) if bold else text_p.render(text, True, color)
    screen.blit(text_surface, (x, y))

def padding (lines,font_size=16):
    return (font_size + font_size/3) * lines

def draw_line(x_cord,y_cord,color=current_theme['lines'],width=1):
    pygame.draw.line(screen, color, x_cord, y_cord, width)
    
def draw_demo_block(x, y, color=None,radius = 8):
    center = (x + radius, y + radius)

    if color == None:
        color = current_theme['text']

    pygame.draw.circle(screen, color, center, radius)
    pygame.draw.circle(screen, current_theme["text"], center, radius, 2)

def draw_all_button(color=None):
    for btn in buttons.values():
        state = btn['state']
        x, y = btn['cord']

        if color == None:
            color = current_theme['text']

        if state:
            check_rect = pygame.Rect(x + 4, y + 4, 8, 8)
            pygame.draw.rect(screen, color, check_rect)

        pygame.draw.rect(screen, color, pygame.Rect(x, y, 16, 16), 2)

def draw_lines():
    for x in range(grid_rect.left, screen_width + 1, block_size):
        pygame.draw.line(screen, current_theme['lines'], (x, 0), (x, screen_height))
        
    for y in range(0, screen_height + 1, block_size):
        pygame.draw.line(screen, current_theme['lines'], (grid_rect.left, y), (screen_width, y))


# helpers
def close_color(block):
    choices = palette[block]
    return random.choice(choices)

def button_check():
    global last_command
    for btn in buttons.values():
        x, y = btn['cord']
        rect = pygame.Rect(x, y, 16, 16)

        if rect.collidepoint(mouse_x, mouse_y):
            btn['state'] = not btn['state']
            last_command = f"{btn['label']} {btn['state']}"
            return 

def grid_cord():
    global grid_x, grid_y
    
    adjusted_x = mouse_x - overlay_size
    
    temp_grid_x = int(adjusted_x / block_size)
    temp_grid_y = int(mouse_y / block_size)

    if 0 <= temp_grid_x < grid_width and  0 <= temp_grid_y < grid_height:
        grid_x = temp_grid_x
        grid_y = temp_grid_y
    
    return grid_x, grid_y

def get_hovered():
    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
        return grid_value[grid_x, grid_y]
    return 0

def is_empty(x, y):
    return not grid_value[x, y]

def is_replacable(x, y,x1,y1):
    before = blocks[grid_value[x,y]]['density']
    after = blocks[grid_value[x1,y1]]['density']
    if before > after :
        return True
    return False

# kind of a fill funtion
# swap block types
# grid_value[x1, y1] = grid_value[x, y]

# swap colors
# grid_color[x1, y1] = grid_color[x, y]

def swap(x, y, x1, y1):  
    # swap block types
    grid_value[x, y], grid_value[x1, y1] = \
    grid_value[x1, y1], grid_value[x, y]

    # swap colors
    grid_color[x, y], grid_color[x1, y1] = \
    grid_color[x1, y1].copy(), grid_color[x, y].copy()

    active_toggle(x, y)
    active_toggle(x1, y1)

def clone(x,y,x1,y1):
    if blocks[grid_value[x,y]]['ability'] == 'clone':
        grid_value[x1, y1] = grid_value[x, y]
        grid_color[x1, y1] = grid_color[x, y]
        active_toggle(x, y)
        active_toggle(x1, y1)
    
def destroy(x, y, x1, y1):
    if blocks[grid_value[x, y]]['ability'] == 'destroy':
        grid_value[x1, y1] = grid_value[x, y]
        grid_color[x1, y1] = grid_color[x, y].copy()

        grid_value[x, y] = 0
        grid_color[x, y] = (0, 0, 0, 0)

        active_toggle(x, y)
        active_toggle(x1, y1)

def move_down(x, y):
    ny = y + 1
    if ny >= grid_height:
        return False

    if is_empty(x, ny):
        swap(x, y, x, ny)
        return True

    if is_replacable(x, y, x, ny):
        if destroy(x, y, x, ny):
            return True
        swap(x, y, x, ny)
        return True

    return False

def move_left(x, y):
    nx = x - 1

    if nx < 0:
        return False

    if is_empty(nx, y) or is_replacable(x, y, nx, y):
        swap(x, y, nx, y)
        return True

    return False

def move_right(x, y):
    nx = x + 1

    if nx >= grid_width:
        return False

    if is_empty(nx, y) or is_replacable(x, y, nx, y):
        swap(x, y, nx, y)
        return True

    return False

def move_down_left(x, y):
    nx = x - 1
    ny = y + 1

    if nx < 0 or ny >= grid_height:
        return False

    if is_empty(nx, ny) or is_replacable(x, y, nx, ny):
        swap(x, y, nx, ny)
        return True

    return False

def move_down_right(x, y):
    nx = x + 1
    ny = y + 1

    if nx >= grid_width or ny >= grid_height:
        return False

    if is_empty(nx, ny) or is_replacable(x, y, nx, ny):
        swap(x, y, nx, ny)
        return True

    return False

def active_toggle(x, y):
    if 0 <= x < grid_width and 0 <= y < grid_height:
        grid_active_next[x, y] = True

    for dx, dy in neighbors_offset:
        mx = x + dx
        my = y + dy
        if 0 <= mx < grid_width and 0 <= my < grid_height:
            grid_active_next[mx, my] = True

def add_neighbour_block(x, y):
    for dx, dy in neighbors_offset:
        if random.randint(0, 1):
            mx = x + dx
            my = y + dy
            if 0 <= mx < grid_width and 0 <= my < grid_height:
                active_toggle(mx,my)
                if selected == 0:
                    grid_value[mx, my] = selected
                    grid_color[mx, my] = blocks[selected]["color"]

                elif not grid_value[mx, my]:
                    grid_value[mx, my] = selected
                    grid_color[mx, my] = close_color(selected)

def simulation_draw_block(x,y):
    block = grid_value[x ,y]
            
    # skip if null
    if block == 0:
        return

    # draw not null
    color = tuple(grid_color[x, y])
    screen_y = block_size * y
    screen_x = overlay_size + block_size * x 
    pygame.draw.rect(screen, color, pygame.Rect(screen_x, screen_y, block_size, block_size))

    if grid_active[x,y] and buttons['debug_btn']['state']:
        pygame.draw.rect(screen, current_theme['lines'], pygame.Rect(screen_x, screen_y, block_size, block_size),1)

    # Skip if paused
    if buttons["pause_btn"]["state"]:
        active_toggle(x,y)
        return
    
    if not grid_active[x,y]:
        return
    
    # grainy solid
    if blocks[block]['name'] == 'sand':
        if move_down(x, y):
            active_toggle(x,y)
            return
        
        if direction:
            if move_down_right(x, y) or move_down_left(x, y):
                active_toggle(x,y)
                return
        else:
            if move_down_left(x, y) or move_down_right(x, y):
                active_toggle(x,y)
                return
    
    # liqued
    if blocks[block]['name'] in ['water','acid']:
        if move_down(x, y):
            active_toggle(x,y)
            return
        
        if direction:
            if move_down_right(x, y) or move_down_left(x, y):
                active_toggle(x,y)
                return
            elif move_right(x, y) or move_left(x, y):
                active_toggle(x,y)
                return
        else:
            if move_down_left(x, y) or move_down_right(x, y):
                active_toggle(x,y)
                return
            elif move_left(x, y) or move_right(x, y):
                active_toggle(x,y)
                return


# left 
def all_overlay():
    # bg and Border
    pygame.draw.rect(screen, current_theme["bg"], overlay_rect)

    draw_line([overlay_size, 0], [overlay_size, screen_height],color=current_theme['text'])
    draw_all_button()

    lines = 1

    # --- fps ---
    current_fps = f'{int(mainclock.get_fps())} FPS'
    draw_text(current_fps, 8, padding(lines),bold = True)
    lines += 2

    # --- selected Selection ---
    draw_text("Selected", 8, padding(lines),bold=True)
    lines += 1
    draw_demo_block(8, padding(lines), blocks[selected]['color'])
    draw_text(blocks[selected]['name'], 32, padding(lines))    

    # --- Buttons ---
    lines += 2
    draw_text('Actions', 8, padding(lines),bold=True)
    for btn in buttons.values():
        lines += 1
        draw_text(btn["label"], 32, padding(lines))
        btn['cord'] = [8 ,padding(lines)]
    
    # --- shortcuts ---
    lines += 2
    draw_text('Blocks', 8, padding(lines),bold=True)
    for key,value in shorcuts.items():
        lines += 1
        draw_demo_block(8, padding(lines), blocks[key]['color'])
        draw_text(f'{value.capitalize()} ({key})', 32, padding(lines))

    # --- debug mode ---
    if buttons['debug_btn']['state']: # stats
        lines += 2
        draw_text("Debug Menu", 8, padding(lines),bold=True)
        lines += 1
        draw_text(f"Grid {grid_width} X {grid_height}", 8, padding(lines))
        lines += 1
        draw_text(f"Total {np.count_nonzero(grid_value)}", 8, padding(lines))    
        lines += 1
        draw_text(f"Moving {np.count_nonzero(grid_active)}", 8, padding(lines))        
        lines+=1
        draw_text(f"Mouse {'pressed' if mouse_pressed else 'released'}", 8, padding(lines))
        lines+=1
        draw_demo_block(8, padding(lines), blocks[hovered]['color'])
        draw_text(f"{blocks[hovered]['name']} hovered", 32, padding(lines))
        lines += 1
        draw_text(f"GX {grid_x}      GY {grid_y}", 8, padding(lines))
        lines += 1
        draw_text(f"MX {mouse_x}   MY {mouse_y}", 8, padding(lines))
        
        
        # Subtitles
        lines += 2
        draw_text("Subtitles", 8, padding(lines),bold=True)
        lines += 1
        draw_text(last_command , 8, padding(lines))

# right
def all_game():
    pygame.draw.rect(screen, current_theme["bg"], grid_rect)

    # grid button
    if buttons["debug_btn"]["state"]:
        draw_lines()

    # Placement logic
    if grid_rect.collidepoint(mouse_x, mouse_y)and mouse_pressed:
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid_value[grid_x, grid_y] = selected
            grid_color[grid_x, grid_y] = close_color(selected)
            active_toggle(grid_x,grid_y)
            
            if not buttons["brush_btn"]["state"]:
                add_neighbour_block(grid_x,grid_y)

    # Simulation and draw logic
    for y in range(grid_height - 1, -1, -1):
        x_order = list(range(grid_width))
        random.shuffle(x_order)
        for x in x_order:
            simulation_draw_block(x, y)
    


# main loop
while run:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = grid_cord()
    direction = not direction

    # event loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            grid_x, grid_y = grid_cord()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pressed = True
            button_check()

        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_pressed = False

        elif event.type == pygame.KEYDOWN:
            key_num = event.key - pygame.K_0
            if key_num in blocks:
                before = selected
                selected = key_num
                last_command = f"{blocks[before]['name']} to {blocks[selected]['name']}"
            if event.key == pygame.K_SPACE:
                buttons['pause_btn']['state'] = not buttons['pause_btn']['state']


    # hoverred block
    hovered = get_hovered()
    
    # theme change 
    current_theme = dark_theme if buttons["dark_btn"]["state"] else  light_theme

    # clear screen
    if buttons["clear_btn"]["state"]:
        grid_value = np.zeros((grid_width, grid_height), dtype=np.uint8)
        grid_color = np.zeros((grid_width, grid_height, 4), dtype=np.uint8)
        buttons["clear_btn"]["state"] = False


    # partations
    all_game()
    all_overlay()

    grid_active[:] = grid_active_next
    grid_active_next.fill(False)

    # update 
    pygame.display.update()
    mainclock.tick(60)