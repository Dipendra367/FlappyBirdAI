"""
flappy.py
Single-file Pygame Flappy Bird clone.

Requirements:
    pip install pygame

Assets:
    Place the following images inside an 'assets/' folder (same folder as this script):
    - base.png
    - bg.png
    - bird1.png
    - bird2.png
    - bird3.png
    - pipe.png

Controls:
    SPACE / UP Arrow -> flap / jump
    ESC or close window -> quit

This version is plain-play (manual). Later we will plug NEAT into this file or import it.
"""

import pygame
import os
import random
import sys

# -----------------------
# CONFIG
# -----------------------
WIN_WIDTH = 576
WIN_HEIGHT = 800
FPS = 30

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')


# -----------------------
# UTILS / ASSET LOADING
# -----------------------
def load_image(name, scale2x=True):
    path = os.path.join(ASSETS_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    if scale2x:
        return pygame.transform.scale2x(img)
    return img


# -----------------------
# Bird class
# -----------------------
class Bird:
    IMGS = []
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        if not Bird.IMGS:
            # lazy load (requires pygame.init())
            Bird.IMGS = [load_image(f"bird{i}.png") for i in (1, 2, 3)]
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = Bird.IMGS[0]

    def jump(self):
        self.vel = -9.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 0.5 * 3 * (self.tick_count ** 2)
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y += d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        idx = (self.img_count // self.ANIMATION_TIME) % len(Bird.IMGS)
        self.img = Bird.IMGS[idx]

        if self.tilt <= -80:
            self.img = Bird.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        blit_rotate_center(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


# -----------------------
# Pipe class
# -----------------------
class Pipe:
    GAP = 150
    VEL = 5

    def __init__(self, x):
        self.x = x
        global PIPE_IMG
        if 'PIPE_IMG' not in globals():
            PIPE_IMG = load_image('pipe.png')
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 350)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        return t_point or b_point


# -----------------------
# Base (ground) class
# -----------------------
class Base:
    VEL = 5
    WIDTH = None
    IMG = None

    def __init__(self, y):
        global BASE_IMG
        if 'BASE_IMG' not in globals():
            BASE_IMG = load_image('base.png')
        Base.IMG = BASE_IMG
        Base.WIDTH = Base.IMG.get_width()
        self.y = y
        self.x1 = 0
        self.x2 = Base.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + Base.WIDTH < 0:
            self.x1 = self.x2 + Base.WIDTH
        if self.x2 + Base.WIDTH < 0:
            self.x2 = self.x1 + Base.WIDTH

    def draw(self, win):
        win.blit(Base.IMG, (self.x1, self.y))
        win.blit(Base.IMG, (self.x2, self.y))


# -----------------------
# Helper: rotate & blit around center
# -----------------------
def blit_rotate_center(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect.topleft)


# -----------------------
# Game functions
# -----------------------
def draw_window(win, bird, pipes, base, score, gen_text=""):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    base.draw(win)
    bird.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    if gen_text:
        gtext = STAT_FONT.render(gen_text, True, (255, 255, 255))
        win.blit(gtext, (10, 10))
    pygame.display.update()


def main():
    pygame.init()
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - Manual Play")
    clock = pygame.time.Clock()

    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(700)]
    score = 0
    run = True

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird.jump()
                if event.key == pygame.K_ESCAPE:
                    run = False
                    break

        bird.move()
        add_pipe = False
        rem = []
        for p in pipes:
            p.move()
            if p.collide(bird):
                draw_window(win, bird, pipes, base, score, gen_text="Crashed!")
                pygame.time.delay(800)
                run = False
            if not p.passed and p.x < bird.x:
                p.passed = True
                add_pipe = True
            if p.x + p.PIPE_TOP.get_width() < 0:
                rem.append(p)
        if add_pipe:
            score += 1
            pipes.append(Pipe(WIN_WIDTH + 100))
        for r in rem:
            pipes.remove(r)

        if bird.y + bird.img.get_height() >= base.y or bird.y < 0:
            draw_window(win, bird, pipes, base, score, gen_text="Hit Ground / Out of bounds")
            pygame.time.delay(800)
            run = False

        base.move()
        draw_window(win, bird, pipes, base, score)

    show_game_over(win, score)
    pygame.quit()
    sys.exit()


def show_game_over(win, score):
    overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    win.blit(overlay, (0, 0))
    big = pygame.font.SysFont("comicsans", 60)
    small = pygame.font.SysFont("comicsans", 30)
    txt = big.render("Game Over", True, (255, 255, 255))
    sc = small.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(txt, ((WIN_WIDTH - txt.get_width()) // 2, WIN_HEIGHT // 2 - 40))
    win.blit(sc, ((WIN_WIDTH - sc.get_width()) // 2, WIN_HEIGHT // 2 + 30))
    pygame.display.update()
    pygame.time.delay(1200)


# -----------------------
# Entrypoint / asset load
# -----------------------
if __name__ == "__main__":
    pygame.init()

    # Fix: set display mode before loading images
    pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    try:
        BG_IMG = pygame.transform.scale(load_image("bg.png", scale2x=False), (WIN_WIDTH, WIN_HEIGHT))
        STAT_FONT = pygame.font.SysFont("comicsans", 30)
    except Exception as e:
        print("Error loading assets. Make sure 'assets/' folder exists with required images.")
        print("Exception:", e)
        pygame.quit()
        sys.exit(1)

    main()

