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
type Cell = tuple[Pixel, Pixel]

class View:
    '''Abstraction class over the raw pygame display to be used by the Model class.

    This class allows the pygame display to be interacted with at the level of macroscopic
    pixels. Note that this class does NOT interact with the user and therefore does NOT
    handle events. The data that this class holds is intentionally kept minimal: only
    pygame components or data that is intimately tied with rendering should be stored here.

    Attributes
    ----------
    px : pix
        The size of each cell in the x direction.
    py : pix
        The size of each cell in the y direction.
    offx : pix
        The offset of the upper left corner of the screen in the x direction relative to the
        upper left corner of the cell (0,0). A positive offset means that the screen is
        left of the (0,0) cell.
    offy : pix
        The equivalent of `offx` in the y direction. A positive offset means that the screen is
        above the (0,0) cell.
    running : bool
        Whether the program is currently in the mainloop.
    '''
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

        self.blinking: list[Cell] = []   # points that have to be rendered with blinking
    
    @property
    def width(self): return self.screen.get_width()
    @property
    def height(self): return self.screen.get_height()

    @property
    def adj_offx(self):
        'The offset taken modulus the cell size in the x direction.'
        return self.offx % self.px

    @property
    def adj_offy(self):
        'The offset taken modulus the cell size in the x direction.'
        return self.offy % self.py

    def get_array_index(self, mx: pix, my: pix) -> Cell:
        '''Convert pixel coordinates to cell coordinates.'''
        return ( int((mx - self.offx) // self.px)
               , int((my - self.offy) // self.py))

    def current_pixel(self) -> Cell:
        '''Get the cell coordinates of the mouse.'''
        mx, my = pygame.mouse.get_pos()
        return self.get_array_index(mx, my)

    def draw_grid(self):
        '''Draws a grid delineating each cell.'''
        for x in frange(self.adj_offx, self.width + self.adj_offx, self.px):
            pygame.draw.line(self.screen, 'white', (x, 0), (x, self.height))
        for y in frange(self.adj_offy, self.height + self.adj_offy, self.py):
            pygame.draw.line(self.screen, 'white', (0, y), (self.width, y))

    def fill_box(self, ix: Pixel, iy: Pixel, color, blink=False):
        '''Fills in a particular cell with the given color.

        Parameters
        ----------
        ix : Pixel
            The x cell coordinate
        iy : Pixel
            The y cell coordinate
        color
            The color. This can be a string, an RGB value, an RGBA value, or anything
            that pygame accepts.
        blink : bool, default=False
            Whether the cell should blink.
        '''
        # upper left corner array coordinates
        ulix, uliy = self.get_array_index(0, 0)
        corrix, corriy = ix - ulix - (self.adj_offx != 0), iy - uliy - (self.adj_offy != 0)
        ulx, uly = (self.offx - self.px) % self.px, (self.offy - self.py) % self.px
        bx, by = corrix * self.px + ulx, corriy * self.py + uly
        wx, wy = min(bx, 0) + self.px, min(by, 0) + self.py
        rect = pygame.Rect(bx, by, wx + 1, wy + 1)
        trans_box = pygame.Surface((self.px + 1, self.py + 1), pygame.SRCALPHA)
        trans_box.fill(color)
 
        if (not blink) or (blink and pygame.time.get_ticks() % 500 > 250):
            self.screen.blit(trans_box, rect)

    def render_array(self, arr, color, blink=False):
        '''Visually represents the given array.

        Given a 2D numpy array representing the boxes that need to be filled in, this
        function will fill in the squares that are truthy with the given color and blink
        attribute. Only the section of the array that is selected by the viewframe
        (which is controlled with `px`, `py`, `offx`, and `offy`) will be rendered. The
        array is treated as cyclic once: that is, it is only wrapped around once.

        Parameters
        ----------
        arr : numpy.ndarray
            The array to be rendered.
        color
            The color. This can be a string, an RGB value, an RGBA value, or anything
            that pygame accepts
        blink : bool, default=False
            Whether the rendered cells should blink.
        '''
        startix, startiy = self.get_array_index(0, 0)
        endix, endiy = self.get_array_index(self.width, self.height)
        rolled_arr = np.roll(arr, (-startix, -startiy), (0, 1))
        for i, row in enumerate(rolled_arr[:endix - startix + 1]):
            for j, elem in enumerate(row[:endiy - startiy + 1]):
                if elem:
                    self.fill_box(i + startix, j + startiy, color, blink=blink)

    def pan(self, dx, dy):
        '''Pan the view frame.

        Parameters
        ----------
        dx : Pixel
            The amount by which the viewframe should be adjusted in the x direction. See the
            class documentation for sign conventions.
        dy : Pixel
            The same as `dx` in the y direction.
        '''
        self.offx += dx * self.px/NAV_SCALE
        self.offy += dy * self.py/NAV_SCALE

    def zoom(self, s: float):
        '''Zoom by a factor relative to the mouse position.

        This function keeps the mouse position in the same position.

        Parameters
        ----------
        s : float
            The zoom factor. Values greater than 1 zoom in, values less than 1 zoom out.'''
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

stroke_size = 1
def stroke_default(mix, miy):
    return [(mix+ix, miy+iy) for ix in range(-stroke_size,stroke_size+1)
                             for iy in range(-stroke_size,stroke_size+1)]

def normalize_points(ps):
    minx, miny = min(p[0] for p in ps), min(p[1] for p in ps)
    maxx, maxy = max(p[0] for p in ps), max(p[1] for p in ps)
    centerx, centery = (minx + maxx)//2, (miny + maxy)//2
    return [(x - centerx, y - centery) for (x, y) in ps]

clipboard = {}
key = ''
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
        self.escape()   # This also defines some properties

        self.mousedown = False
        self.remove = False      # whether items are added or not

        self.keypress_log = deque([0]*KEYPRESS_LOG_SIZE, maxlen=KEYPRESS_LOG_SIZE)

    def escape(self, reset_stroke_style=True):
        global stroke_size    # This is bad...
        self.stroke = set()
        self.mode = Mode.WRITE
        if reset_stroke_style:
            self.stroke_style = stroke_default
            stroke_size = 0

    def onQuit(self, _, view):  # can def be moved to view
        view.running = False

    def onMouseButtonDown(self, _, view):
        self.mousedown = True
        match self.mode:
            case Mode.WRITE:
                self.remove = self.arr[view.current_pixel()]
            case Mode.SELECT:
                self.remove = view.current_pixel() in self.stroke

    def onMouseButtonUp(self, _, view):
        self.mousedown = False
        match self.mode:
            case Mode.WRITE:
                for coords in self.stroke:
                    self.arr[coords] = not self.remove
                self.stroke = set()
            case Mode.SELECT:
                # This is handled in the mouse motion
                pass

    def onKeyDown(self, ev, view):    # nonrepeatable bindings
        global stroke_size    # This is very bad...
        global clipboard      # TODO: Make a model variable
        global key
        match ev.key:
            case pygame.K_s: self.mode = Mode.SELECT
            case pygame.K_ESCAPE: self.escape()
            # temporary bindings
            case pygame.K_q: stroke_size = max(stroke_size - 1, 0)
            case pygame.K_w: stroke_size += 1
            case clipkey if self.keypress_log[-1] == pygame.K_y:
                print('copy')
                clipboard[clipkey] = normalize_points([p for p in self.stroke if self.arr[p]])
                self.escape(reset_stroke_style=False)
                self.keypress_log.pop()
            case clipkey if self.keypress_log[-1] == pygame.K_p:
                print('paste', clipkey in clipboard)
                key = clipkey
                self.stroke_style = stroke_paste
                self.keypress_log.pop()
            case clipkey:
                self.keypress_log.append(clipkey)

    def handle_key(self, keycode, view):   # repeatable bindings
        match keycode:
            case pygame.K_UP: view.pan(0,1)
            case pygame.K_DOWN: view.pan(0,-1)
            case pygame.K_LEFT: view.pan(1,0)
            case pygame.K_RIGHT: view.pan(-1,0)
            # temporary bindings
            case pygame.K_l: view.zoom(1.01)
            case pygame.K_k: view.zoom(1/1.01)
            # debug bindings
            case pygame.K_RETURN:
                print(f'{get_array_index(mx, my)=}, {offx=}, {offy=}, {mx=}, {my=}')


    def handle_mouse(self, mix, miy, view):
        if self.mousedown:
            if self.mode == Mode.SELECT and self.remove:
                # This is mainly a stylistic thing
                self.stroke.difference_update(self.stroke_style(mix, miy))
            else:
                self.stroke.update(self.stroke_style(mix, miy))
        for ix, iy in self.stroke_style(mix, miy):
            view.fill_box(ix, iy, 'yellow')

    def render(self, view):
        view.render_array(self.arr, 'purple')
        is_select = self.mode == Mode.SELECT
        color = (255,255,255,100) if is_select else 'green'
        for ix, iy in self.stroke:
            view.fill_box(ix, iy, color, blink=is_select)

view = View(px = 15, py = 15, offx = 0, width = WIDTH, height = HEIGHT, offy = 0)
model = Model()

keycodes: list[int] = [getattr(pygame, x) for x in dir(pygame) if x.startswith('K_')]

while view.running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        fn = getattr(model, 'on' + pygame.event.event_name(event.type), None)
        if fn is not None: fn(event, view)

    # repeatable (smooth) keybindings
    keys = pygame.key.get_pressed()
    for key in keycodes:
        if keys[key]: model.handle_key(key, view)

    # fill the screen with a color to wipe away anything from last frame
    view.screen.fill("black")   # TODO: fix

    model.render(view)

    model.handle_mouse(*view.current_pixel(), view)
    view.draw_grid()

    # flip() the display to put your work on screen
    pygame.display.flip()

    view.clock.tick(60)  # limits FPS to 60   TODO fix

pygame.quit()
