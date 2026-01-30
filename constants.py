### Constants ###
# Visuals config
WIDTH = 1280
HEIGHT = 720
FPS = 60

START_PX = 15
START_PY = 15

# NAV_SPEED is speed of navigation, higher is slower
NAV_SPEED = 1/10
ZOOM_SPEED = 1.01
# How many past keypresses to store
KEYPRESS_LOG_SIZE = 1000

ARRAY_SHAPE = (1000,1000)

# TODO: make a color also include blink (structured data)
BG_COLOR = 'black'
CURSOR_COLOR = 'yellow'
ELEM_COLOR = 'purple'
SELECT_COLOR = (255,255,255,100)
STROKE_COLOR = 'green'

### Types ###

# px is an actual, screen pixel
# Pixel is the rendered box units
type pix = int
type Pixel = int
type Cell = tuple[Pixel, Pixel]

def normalize_points(ps):
    minx, miny = min(p[0] for p in ps), min(p[1] for p in ps)
    maxx, maxy = max(p[0] for p in ps), max(p[1] for p in ps)
    centerx, centery = (minx + maxx)//2, (miny + maxy)//2
    return [(x - centerx, y - centery) for (x, y) in ps]

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


