import pygame
import numpy as np

WIDTH = 1280
HEIGHT = 720

ARRAY_SHAPE = (1000,1000)

# NAV_SCALE is speed of navigation, higher is slower
NAV_SCALE = 10

# pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True

px = 30
py = 30

offx = 0
offy = 0

def draw_grid(screen):
    width, height = screen.get_size()
    adj_offx = offx % px
    adj_offy = offy % py
    for x in range(adj_offx, width + adj_offx, px):
        pygame.draw.line(screen, 'white', (x, 0), (x, height))
    for y in range(adj_offy, height + adj_offy, py):
        pygame.draw.line(screen, 'white', (0, y), (width, y))

def get_array_index(mx, my):
    return ((mx - offx) // px, (my - offy) // py)

def fill_box(screen, ix, iy, color):
    # upper left corner array coordinates
    ulix, uliy = get_array_index(0, 0)
    corrix, corriy = ix - ulix - (offx % 30 != 0), iy - uliy - (offy % 30 != 0)
    ulx, uly = (offx - px) % px, (offy - py) % px
    bx, by = corrix * px + ulx, corriy * py + uly
    wx, wy = min(bx, 0) + px, min(by, 0) + py
    rect = pygame.Rect(bx, by, wx, wy)
    screen.fill(color, rect=rect)

arr = np.zeros(ARRAY_SHAPE)

stroke = set()
mousedown = False # There has to be a bettery way of doing this
strokemode = 0

mx, my = 0, 0
while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mousedown = True
            strokemode = not arr[get_array_index(mx, my)]
        if event.type == pygame.MOUSEBUTTONUP:
            for coords in stroke:
                arr[coords] = strokemode
            stroke = set()
            mousedown = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        offy += py//NAV_SCALE
    elif keys[pygame.K_DOWN]:
        offy -= py//NAV_SCALE
    elif keys[pygame.K_LEFT]:
        offx += px//NAV_SCALE
    elif keys[pygame.K_RIGHT]:
        offx -= px//NAV_SCALE
    elif keys[pygame.K_RETURN]:
        print(f'{get_array_index(mx, my)=}, {offx=}, {offy=}, {mx=}, {my=}')

    if mousedown:
        stroke.add(get_array_index(mx, my))

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    startix, startiy = get_array_index(0, 0)
    endix, endiy = get_array_index(WIDTH, HEIGHT)
    for i, row in enumerate(arr[startix:endix]):   # check ordering!
        for j, elem in enumerate(row[startiy:endiy]):
            if elem:
                fill_box(screen, i + startix, j + startiy, 'purple')
    for box in stroke:
        fill_box(screen, *box, 'green')

    mx, my = pygame.mouse.get_pos()
    fill_box(screen, *get_array_index(mx, my), 'yellow')
    draw_grid(screen)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
