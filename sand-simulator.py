import pygame as pygame
import numpy as np
import random as rd

pygame.init()
mainclock = pygame.time.Clock()

# main variables
screen_size= 600
overlay_size = 200

# screen
screen_height = screen_size
screen_width = screen_size + overlay_size
screen = pygame.display.set_mode((screen_width, screen_height)) 

# theme
dark_theme = {'bg': (20, 20, 20),'lines': (80, 80, 80), 'muted': (180, 180, 180), 'text': (240, 240, 240)}
light_theme = {'bg': (240, 240, 240),'lines': (220, 220, 220), 'muted': (80, 80, 80), 'text': (40, 40, 40)}
theme = dark_theme

# variables
run = True
overlay_width  = 180
block_size = int(screen_size/100)
overlay_rect = pygame.Rect(0,0,overlay_width,screen_height)
grid_rect = pygame.Rect(overlay_width,0,screen_width - overlay_width,screen_height)
paragraph = pygame.font.SysFont('Arial', 16)
small_mouse = [(0, -1), (-1,  0), (1,  0), (0,  1)]
big_mouse = [(-2, -2), (0, -2), (2, -2), (-2,  0), (2,  0), (-2,  2), (0,  2), (2,  2)]
neighbors_offset = [(-1, -1), (0, -1), (1, -1), (-1,  0), (1,  0), (-1,  1), (0,  1), (1,  1)]
grid_width = int((screen_width - overlay_width) / block_size)
grid_height = int(screen_height / block_size)
grid = np.zeros((grid_width, grid_height, 4), dtype=int)

# user variable
grid_x = 0 
grid_y = 0
mouse_x = 0
mouse_y = 0
selected = 1
hovered = 0
mouse_pressed = False
last_command = "No command yet"

blocks = {  0 : {'name': 'void', 'color': (255, 255, 255) ,'density':0},
            1 : {'name': 'sand', 'color': (194, 178, 128) ,'density':4},
            2 : {'name': 'stone','color': (112, 128, 144) ,'density':6},
            3 : {'name': 'water','color': (0  , 0  , 255) ,'density':2},}

buttons = { "pause_btn": {"state": False, "cord": [0, 0], "label":'Pause game'},
            "clear_btn": {"state": False, "cord": [0, 0], "label":'Clear screen'},
            "theme_btn": {"state": False, "cord": [0, 0], "label":'Dark theme'},
            "lines_btn": {"state": True , "cord": [0, 0], "label":'Grid lines'},
            "brush_btn": {"state": True , "cord": [0, 0], "label":'Thick brush'},
            }

shorcuts = {'Space': 'Pause'}
for num,block in blocks.items():
    shorcuts.update({str(num):block['name']})

# draw helpers
def draw_text(text, x, y, color=None):
    if color is None:
        color = theme['text']
    text_surface = paragraph.render(text, True, color)
    screen.blit(text_surface, (x, y))

def padding (lines,font_size=16):
    return (font_size + font_size/4) * lines

def draw_line(x_cord,y_cord,color=theme['lines'],width=1):
    pygame.draw.line(screen, color, x_cord, y_cord, width)
    
def draw_block_indicator(x,y,color=theme['muted']):
    pygame.draw.rect(screen,color,pygame.Rect(x,y,16,16))
    pygame.draw.rect(screen,theme["lines"],pygame.Rect(x,y,16,16),1)

def draw_button(color=theme['muted']):
    for btn in buttons.values():
        state = btn['state']
        x, y = btn['cord']

        if state:
            pygame.draw.rect(screen, color, pygame.Rect(x + 4, y + 4, 8, 8))

        pygame.draw.rect(screen, color, pygame.Rect(x, y, 16, 16), 1)

def draw_lines():
    for x in range(grid_rect.left, screen_width + 1, block_size):
        pygame.draw.line(screen, theme['lines'], (x, 0), (x, screen_height))
        
    for y in range(0, screen_height + 1, block_size):
        pygame.draw.line(screen, theme['lines'], (grid_rect.left, y), (screen_width, y))

def draw_brush():
    points = big_mouse if buttons['brush_btn']['state'] else small_mouse
    for dx, dy in points:
        gx = grid_x + dx
        gy = grid_y + dy

        if not (0 <= gx < grid_width and 0 <= gy < grid_height):
            continue

        px = overlay_width + gx * block_size
        py = gy * block_size

        pygame.draw.rect(
            screen,
            theme['text'],
            pygame.Rect(px, py, block_size, block_size),
            1
        )


# helpers
def close_color(selected, delta = 8):
    r, g, b = blocks[selected]['color']
    return (
        max(0, min(255, r + rd.randint(-delta, delta))),
        max(0, min(255, g + rd.randint(-delta, delta))),
        max(0, min(255, b + rd.randint(-delta, delta))),
    )

def button_check():
    global last_command
    for name, btn in buttons.items():
        x, y = btn['cord']
        rect = pygame.Rect(x, y, 16, 16)

        if rect.collidepoint(mouse_x, mouse_y):
            btn['state'] = not btn['state']
            last_command = f"{btn['label']} = {btn['state']}"

def grid_cord():
    global grid_x, grid_y
    
    adjusted_x = mouse_x - overlay_width
    
    temp_grid_x = int(adjusted_x / block_size)
    temp_grid_y = int(mouse_y / block_size)

    if 0 <= temp_grid_x < grid_width:
        grid_x = temp_grid_x
    if 0 <= temp_grid_y < grid_height:
        grid_y = temp_grid_y
    
    return grid_x, grid_y

def get_hovered():
    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
        return grid[grid_x, grid_y, 0]
    return 0

def is_empty(x, y):
    return not grid[x, y, 0]

def is_replacable(x, y,x1,y1):
    before = blocks[grid[x,y,0]]['density']
    after = blocks[grid[x1,y1,0]]['density']
    if before > after :
        return True
    return False

def swap(x1, y1, x2, y2):
    tmp = grid[x1, y1].copy()
    grid[x1, y1] = grid[x2, y2]
    grid[x2, y2] = tmp

def move_down(x, y):
    ny = y + 1
    if ny >= grid_height:
        return False

    if is_empty(x, ny) or is_replacable(x, y, x, ny):
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

def add_neighbours(x, y):
    for dx, dy in neighbors_offset:
        if rd.randint(0, 1):
            mx = x + dx
            my = y + dy
            if 0 <= mx < grid_width and 0 <= my < grid_height:
                if selected == 0:
                    grid[mx, my, 0] = selected
                    grid[mx, my, 1:4] = blocks[selected]["color"]

                elif not grid[mx, my, 0]:
                    grid[mx, my, 0] = selected
                    grid[mx, my, 1:4] = close_color(selected)


# left 
def all_overlay():
    # bg and Border
    pygame.draw.rect(screen, theme["bg"], overlay_rect)

    draw_line([overlay_width, 0], [overlay_width, screen_height],color=theme['text'])
    draw_button()

    lines = 1

    # --- fps ---
    current_fps = int(mainclock.get_fps())
    draw_text(f'Fps: {current_fps}', 16, padding(lines))
    lines += 2

    # --- selected Selection ---
    draw_text(f"Selected: {blocks[selected]['name']}", 16, padding(lines))
    draw_block_indicator(overlay_size - 50, padding(lines), blocks[selected]['color'])
    lines += 2

    # --- Hovered Block ---
    draw_text(f"Hovered: {blocks[hovered]['name']}", 16, padding(lines))
    draw_block_indicator(overlay_size - 50, padding(lines), blocks[hovered]['color'])
    lines += 2

    # --- Mouse ---
    draw_text("Mouse", 16, padding(lines))
    lines += 1
    draw_text(f"Pressed: {mouse_pressed}", 16, padding(lines))
    lines += 1
    draw_text(f"X: {mouse_x}", 16, padding(lines))
    lines += 1
    draw_text(f"Y: {mouse_y}", 16, padding(lines))
    
    # --- Subtitles ---
    lines += 2
    draw_text("Subtitles:", 16, padding(lines))
    lines += 1
    draw_text(last_command , 16, padding(lines))
    

    # --- Buttons ---
    lines += 1
    for btn in buttons.values():
        lines += 1
        draw_text(btn["label"], 16, padding(lines))
        btn['cord'] = [overlay_size - 50 ,padding(lines)]
    
    # --- shortcuts ---
    lines += 1
    for key,value in shorcuts.items():
        lines += 1
        draw_text(f'{key} : {value} ', 16, padding(lines))


# right
def all_game():
    pygame.draw.rect(screen, theme["bg"], grid_rect)

    # grid button
    if buttons["lines_btn"]["state"]:
        draw_lines()

    # Placement logic
    if mouse_pressed:
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            grid[grid_x, grid_y, 0] = selected
            grid[grid_x, grid_y, 1:4] = close_color(selected)
            if buttons["brush_btn"]["state"]:
                add_neighbours(grid_x,grid_y)

    # Simulation and draw logic
    for y in range(grid_height - 1, -1, -1):
        for x in range(grid_width):
            block = grid[x ,y, 0]
            
            # skip if null
            if block == 0:
                continue

            # draw not null
            color = (grid[x, y, 1:4])
            screen_x = overlay_width + block_size * x 
            screen_y = block_size * y
            pygame.draw.rect(screen, color, pygame.Rect(screen_x, screen_y, block_size, block_size))

            # Skip if paused
            if buttons["pause_btn"]["state"]:
                continue
            
            # sand
            if blocks[block]['name'] == 'sand':
                if move_down(x, y):
                    continue

                if rd.choice((True, False)):
                    if move_down_left(x, y) or move_down_right(x, y):
                        continue
                else:
                    if move_down_right(x, y) or move_down_left(x, y):
                        continue
            
            # water
            if blocks[block]['name'] == 'water':
                if move_down(x, y):
                    continue
                if move_down_right(x, y) or move_down_left(x, y):
                    continue
                if move_right(x, y) or move_left(x, y):
                    continue

    draw_brush()
    
    
    

# main loop
while run:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_x, grid_y = grid_cord()
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
    theme = dark_theme if buttons["theme_btn"]["state"] else  light_theme

    # clear screen
    if buttons["clear_btn"]["state"]:
        grid = np.zeros((grid_width, grid_height, 4), dtype=int)
        buttons["clear_btn"]["state"] = False


    # Clear screen
    screen.fill(theme['bg'])

    # partations
    all_game()
    all_overlay()

    # update 
    pygame.display.update()
    mainclock.tick(60)