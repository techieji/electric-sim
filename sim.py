import pygame
import numpy as np
from enum import Enum
from collections import deque

### Constants ###
# Should probably be broken out

WIDTH = 1280
HEIGHT = 720

ARRAY_SHAPE = (1000,1000)

# NAV_SCALE is speed of navigation, higher is slower
NAV_SCALE = 10
# How many past keypresses to store
KEYPRESS_LOG_SIZE = 1000

### Useful functions ###

def frange(start, stop, step=1): # only ascending
    i = 0
    while i*step + start < stop:
        yield i*step + start
        i += 1

# px is an actual, screen pixel
# Pixel is the rendered box units
type pix = int
type Pixel = int


class View:
    def __init__(self, px: pix, py: pix, width: pix, height: pix, offx: pix=0, offy: pix=0):
        # size of each pixel
        self.px = px
        self.py = py
        # the view frame's offset (in real pixels)
        self.offx = offx
        self.offy = offy

        pygame.init()
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
    
    @property
    def width(self): return self.screen.get_width()
    @property
    def height(self): return self.screen.get_height()

    @property
    def adj_offx(self): return self.offx % self.px
    def adj_offy(self): return self.offy % self.py

    def get_array_index(self, mx: pix, my: pix) -> tuple[Pixel, Pixel]:
        return ( int((mx - self.offx) // self.px)
               , int((my - self.offy) // self.py))

    def current_pixel(self) -> tuple[Pixel, Pixel]:
        mx, my = pygame.mouse.get_pos()
        return self.get_array_index(mx, my)

    def draw_grid(self):
        for x in frange(adj_offx, self.width + self.adj_offx, self.px):
            pygame.draw.line(self.screen, 'white', (x, 0), (x, self.height))
        for y in frange(adj_offy, self.height + self.adj_offy, self.py):
            pygame.draw.line(self.screen, 'white', (0, y), (self.width, y))

    def fill_box(self, ix: Pixel, iy: Pixel, color,
                 draw_fn=lambda screen,rect,color: screen.fill(color, rect=rect)):
        # upper left corner array coordinates
        ulix, uliy = self.get_array_index(0, 0)
        corrix, corriy = ix - ulix - (self.adj_offx != 0), iy - uliy - (self.adj_offy != 0)
        ulx, uly = (self.offx - self.px) % self.px, (self.offy - self.py) % self.px
        bx, by = corrix * self.px + ulx, corriy * self.py + uly
        wx, wy = min(bx, 0) + self.px, min(by, 0) + self.py
        rect = pygame.Rect(bx, by, wx + 1, wy + 1)
        draw_fn(self.screen, rect, color)

    def pan(self, dx, dy):
        self.offx += dx * self.px//NAV_SCALE
        self.offy += dy * self.py//NAV_SCALE

    def zoom(self, s: float):
        mx, my = pygame.mouse.get_pos()
        self.offx = (self.offx - mx) * s + mx 
        self.offy = (self.offy - my) * s + my
        self.px *= s
        self.py *= s

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

class Mode(Enum):
    WRITE = 1
    SELECT = 2

class Model:
    def __init__(self, arr=None):
        self.arr = np.zeros(ARRAY_SHAPE) if arr is None else arr
        self.escape()

        self.mousedown = False
        self.remove = False      # whether items are added or not

        self.keypress_log = deque([0]*KEYPRESS_LOG_SIZE, maxsize=KEYPRESS_LOG_SIZE)

    def escape(self, reset_stroke_style=True):
        global stroke_size    # This is bad...
        self.stroke = set()
        self.mode = Mode.WRITE
        if reset_stroke_style
            self.stroke_style = stroke_default
            stroke_size = 0

    def onQuit(self, _, view):  # can def be moved to view
        view.running = False

    def onMouseButtonDown(self, _, view):
        self.mousedown = True
        match self.mode:
            case Mode.WRITE:
                self.remove = arr[view.current_pixel()]
            case Mode.SELECT:
                self.remove = view.current_pixel() in selection

    def onMouseButtonUp(self, _, view):
        self.mousedown = False
        match self.mode:
            case Mode.WRITE:
                for coords in self.stroke:
                    self.arr[coords] = not self.remove
                self.stroke = set()
            case Mode.SELECT:
                # will be implicitly handled by not resetting the stroke
                pass

    def onKeyDown(self, ev, view):    # nonrepeatable bindings
        global stroke_size    # This is very bad...
        match ev.key:
            case pygame.K_s: self.mode = Mode.SELECT
            case pygame.K_ESCAPE: self.escape()
            # temporary bindings
            case pygame.K_q: stroke_size = max(stroke_size - 1, 0)
            case pygame.K_q: stroke_size += 1
            case pygame.K_p: self.stroke_style = stroke_paste
            case key if self.keypress_log[-1] == pygame.K_y:
                clipboard[key] = normalize_points([p for p in self.stroke if self.arr[p]])
                self.escape(reset_stroke_style=False)

    def handleKey(self, keycode, view):   # repeatable bindings
        match keycode:
            case pygame.K_UP: view.pan(0,1)
            case pygame.K_DOWN: view.pan(0,-1)
            case pygame.K_LEFT: view.pan(1,0)
            case pygame.K_RIGHT: view.pan(-1,0)
            # temporary bindings
            case pygame.K_l: view.zoom(1.01)
            case pygame.K_k: view.zoom(1/1.01)

view = View(px = 15, py = 15, offx = 0, WIDTH, HEIGHT, offy = 0)
model = Model()

keycodes: list[int] = [getattr(pygame, x) for x in dir(pygame) if x.startswith('K_')]

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        fn = getattr(model, 'on' + pygame.event.event_name(event), None)
        if fn is not None: fn(event, view)

    # repeatable (smooth) keybindings
    keys = pygame.key.get_pressed()
    for key in keycodes:
        if keys[key]: model.handleKey(key, view)


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
