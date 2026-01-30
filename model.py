from constants import *
import pygame
import numpy as np
from enum import Enum
from collections import deque

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
            case pygame.K_UP: view.pan(0,NAV_SPEED)
            case pygame.K_DOWN: view.pan(0,-NAV_SPEED)
            case pygame.K_LEFT: view.pan(NAV_SPEED,0)
            case pygame.K_RIGHT: view.pan(-NAV_SPEED,0)
            # temporary bindings
            case pygame.K_l: view.zoom(ZOOM_SPEED)
            case pygame.K_k: view.zoom(1/ZOOM_SPEED)
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
            view.fill_box(ix, iy, CURSOR_COLOR)

    def render(self, view):
        view.render_array(self.arr, ELEM_COLOR)
        is_select = self.mode == Mode.SELECT
        color = SELECT_COLOR if is_select else STROKE_COLOR
        for ix, iy in self.stroke:
            view.fill_box(ix, iy, color, blink=is_select)


