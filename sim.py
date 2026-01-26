import pygame

WIDTH = 1280
HEIGHT = 720

NAV_SCALE = 5

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
    adj_offx = offx % px
    adj_offy = offy % py
    for x in range(adj_offx, WIDTH + adj_offx, px):
        pygame.draw.line(screen, 'white', (x, 0), (x, HEIGHT))
    for y in range(adj_offy, HEIGHT + adj_offy, py):
        pygame.draw.line(screen, 'white', (0, y), (WIDTH, y))

def get_array_index(mx, my):
    return ((mx - offx) // px, (my - offy) // py)

mx, my = 0, 0
while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                offy += py//NAV_SCALE
            elif event.key == pygame.K_DOWN:
                offy -= py//NAV_SCALE
            elif event.key == pygame.K_LEFT:
                offx += px//NAV_SCALE
            elif event.key == pygame.K_RIGHT:
                offx -= px//NAV_SCALE
            elif event.key == pygame.K_RETURN:
                print(get_array_index(mx, my))

    # fill the screen with a color to wipe away anything from last frame
    screen.fill("black")

    draw_grid(screen)

    mx, my = pygame.mouse.get_pos()
    screen.fill('yellow', rect=pygame.Rect(
        ((mx - (offx % px)) // px) * px + (offx % px),
        ((my - (offy % py)) // py) * py + (offy % py),
        px, py))

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
