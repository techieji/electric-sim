from constants import *         # TODO: make more specific
import pygame
import numpy as np

def frange(start, stop, step=1):
    '''Range function that supports floats.

    This function does not accumulate errors. When
    `step` > 0, requires that `start` < `stop`. When
    `step` = 0, then `stop` < `start`.
    '''
    i = 0
    while i*step + start < stop:
        yield i*step + start
        i += 1

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

    def prep_frame_and_tick(self):
        '''Prepares the screen for drawing and controls the framerate.'''
        self.screen.fill(BG_COLOR)
        self.clock.tick(FPS)
    
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
        self.offx += dx * self.px
        self.offy += dy * self.py

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
