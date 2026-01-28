import pygame
import numpy as np

WIDTH = 1280
HEIGHT = 720

ARRAY_SHAPE = (1000,1000)

# NAV_SCALE is speed of navigation, higher is slower
NAV_SCALE = 10

# pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
running = True

px = 15
py = 15

offx = 0
offy = 0

def frange(start, stop, step=1): # only ascending
    i = 0
    while i*step + start < stop:
        yield i*step + start
        i += 1

def draw_grid(screen):
    width, height = screen.get_size()
    adj_offx = offx % px
    adj_offy = offy % py
    for x in frange(adj_offx, width + adj_offx, px):
        pygame.draw.line(screen, 'white', (x, 0), (x, height))
    for y in frange(adj_offy, height + adj_offy, py):
        pygame.draw.line(screen, 'white', (0, y), (width, y))

def get_array_index(mx, my):
    return (int((mx - offx) // px), int((my - offy) // py))

def fill_box(screen, ix, iy, color,
             draw_fn=lambda screen,rect,color: screen.fill(color, rect=rect)):
    # upper left corner array coordinates
    ulix, uliy = get_array_index(0, 0)
    corrix, corriy = ix - ulix - (offx % px != 0), iy - uliy - (offy % py != 0)
    ulx, uly = (offx - px) % px, (offy - py) % px
    bx, by = corrix * px + ulx, corriy * py + uly
    wx, wy = min(bx, 0) + px, min(by, 0) + py
    rect = pygame.Rect(bx, by, wx + 1, wy + 1)
    draw_fn(screen, rect, color)

def zoom(s, mx, my):
    global offx, offy, px, py
    offx = (offx-mx)*s + mx 
    offy = (offy-my)*s + my
    px *= s
    py *= s

# ======== Variables and functions for the algorithm ========
VERTICES_NOT = []
VERTICES_TOGGLE = []

SHAPE_NOT = (1,1,1,1,1,0,1,1,1)
SHAPE_TOGGLE = (1,1,1,1,1,1,1,1,1)

# Checks if a given position is the center of a shape
# @param ix, iy is upper-left corner of box to be checked
# @return boolean 1 if found 
def compare(ix, iy, shape):
    global arr
    for i in range(0,shape.count()):
        # TODO: implement checking for shapes of other dimensions
        if arr[ix + i%3][iy + i//3] != shape[i]:
            return 0
    return 1

# Iterates over board or region running compare to record vertices of shapes
def find_shapes():
    return 0

# Colors the circuit by iterating through the graph until reaching a marked vertex
def color():
    return 0

### Strokes #######
# This should probably be split out into another file?

stroke_size = 0
def stroke_default(mix, miy):
    return [(mix+ix, miy+iy) for ix in range(-stroke_size,stroke_size+1)
                             for iy in range(-stroke_size,stroke_size+1)]

def normalize_points(ps):
    minx, miny = min(p[0] for p in ps), min(p[1] for p in ps)
    maxx, maxy = max(p[0] for p in ps), max(p[1] for p in ps)
    centerx, centery = (minx + maxx)//2, (miny + maxy)//2
    return [(x - centerx, y - centery) for (x, y) in ps]

clipboard = {}
key = 'a'
def stroke_paste(mix, miy):
    if key not in clipboard: return stroke_default(mix, miy)
    return [(x+mix, y+miy) for (x, y) in clipboard[key]]

###################

arr = np.zeros(ARRAY_SHAPE)

stroke = set()
stroke_style = stroke_default
mousedown = False # There has to be a better way of doing this
strokemode = 0
selectmode = 0

select = False
selection = set()

mx, my = 0, 0
while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mousedown = True
            selectmode = get_array_index(mx, my) not in selection
            strokemode = not arr[get_array_index(mx, my)]
        elif event.type == pygame.MOUSEBUTTONUP:
            if select:
                if selectmode:
                    selection.update(stroke)
                else:
                    selection.difference_update(stroke)
            else:
                for coords in stroke:
                    arr[coords] = strokemode
            stroke = set()
            mousedown = False
        elif event.type == pygame.KEYDOWN:
            # non-repeatable (non-smooth) key bindings
            if event.key == pygame.K_s:
                select = True
            elif event.key == pygame.K_ESCAPE:
                select = False
                selection = set()
                stroke_style = stroke_default
                stroke_size = 1
            elif event.key == pygame.K_q:   # temporary stroke size bindings
                stroke_size = max(stroke_size - 1, 0)
            elif event.key == pygame.K_w:
                stroke_size += 1
            elif event.key == pygame.K_y and select:
                clipboard['a'] = normalize_points([p for p in selection if arr[p]])
                selection = set()
                select = False
            elif event.key == pygame.K_p:
                stroke_style = stroke_paste

    # repeatable (smooth) keybindings
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        offy += py//NAV_SCALE
    elif keys[pygame.K_DOWN]:
        offy -= py//NAV_SCALE
    elif keys[pygame.K_LEFT]:
        offx += px//NAV_SCALE
    elif keys[pygame.K_RIGHT]:
        offx -= px//NAV_SCALE
    elif keys[pygame.K_l]:   # temporary zoom bindings
        zoom(1.01, mx, my)
    elif keys[pygame.K_k]:
        zoom(1/1.01, mx, my)

    if mousedown:
        stroke.update(stroke_style(*get_array_index(mx, my)))

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    startix, startiy = get_array_index(0, 0)
    endix, endiy = get_array_index(*screen.get_size())
    rolled_arr = np.roll(arr, (-startix, -startiy), (0, 1))
    for i, row in enumerate(rolled_arr[:endix - startix + 1]):   # check ordering!
        for j, elem in enumerate(row[:endiy - startiy + 1]):
            if elem:
                fill_box(screen, i + startix, j + startiy, 'purple')
    for box in stroke:
        fill_box(screen, *box, 'green')

    if pygame.time.get_ticks() % 500 > 250:
        gray_box = pygame.Surface((px + 1, py + 1), pygame.SRCALPHA)
        gray_box.fill((255, 255, 255, 150))
        for box in selection:
            fill_box(screen, *box, 'gray', lambda screen, rect, color: screen.blit(gray_box, rect))

    if keys[pygame.K_RETURN]:
        print(f'{get_array_index(mx, my)=}, {offx=}, {offy=}, {mx=}, {my=}')

    mx, my = pygame.mouse.get_pos()
    for box in stroke_style(*get_array_index(mx, my)):
        fill_box(screen, *box, 'yellow')
    #draw_grid(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
