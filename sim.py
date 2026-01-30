import pygame
from model import Model
from view import View
from constants import *

view = View(px = START_PX, py = START_PY, offx = 0, offy = 0, width = WIDTH, height = HEIGHT)
model = Model()

keycodes: list[int] = [getattr(pygame, x) for x in dir(pygame) if x.startswith('K_')]

while view.running:
    for event in pygame.event.get():
        fn = getattr(model, 'on' + pygame.event.event_name(event.type), None)
        if fn is not None: fn(event, view)

    # repeatable (smooth) keybindings
    keys = pygame.key.get_pressed()
    for key in keycodes:
        if keys[key]: model.handle_key(key, view)

    # fill the screen with a color to wipe away anything from last frame
    view.prep_frame_and_tick()
    model.render(view)
    model.handle_mouse(*view.current_pixel(), view)
    view.draw_grid()

    # flip() the display to put your work on screen
    pygame.display.flip()

pygame.quit()
