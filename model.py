from constants import *
import pygame
import numpy as np
from enum import Enum
from collections import deque
from dataclasses import asdict
from strokes import StrokeParams, stroke_default, stroke_paste

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
        self.stroke_params = StrokeParams()

    def escape(self, reset_stroke_style=True):
        self.stroke = set()
        self.mode = Mode.WRITE
        if reset_stroke_style:
            self._stroke_style = stroke_default
            stroke_size = 0

    @property
    def stroke_style(self):
        return self._stroke_style(**asdict(self.stroke_params))

    def onQuit(self, _, view):
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
        match ev.key:
            case pygame.K_s: self.mode = Mode.SELECT
            case pygame.K_ESCAPE: self.escape()
            # temporary bindings
            case pygame.K_q:
                self.stroke_params.stroke_size = max(self.stroke_params.stroke_size - 1, 0)
            case pygame.K_w: self.stroke_params.stroke_size += 1
            case clipkey if self.keypress_log[-1] == pygame.K_y:
                print('copy')
                self.stroke_params.clipboard[clipkey] = normalize_points([p for p in self.stroke if self.arr[p]])
                self.escape(reset_stroke_style=False)
                self.keypress_log.pop()
            case clipkey if self.keypress_log[-1] == pygame.K_p:
                print('paste')
                self.stroke_params.key = clipkey
                self._stroke_style = stroke_paste
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


