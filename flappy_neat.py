"""
Flappy Bird AI using NEAT
Requirements:
    pip install pygame neat-python
Assets:
    Place in 'assets/':
    - base.png
    - bg.png
    - bird1.png, bird2.png, bird3.png
    - pipe.png
Controls:
    None needed — AI plays automatically
"""

import pygame
import os
import random
import sys
import neat

# -----------------------
# CONFIG
# -----------------------
WIN_WIDTH = 576
WIN_HEIGHT = 800
FPS = 30
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')

# -----------------------
# Load images
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
            Bird.IMGS = [load_image(f"bird{i}.png") for i in (1,2,3)]
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = Bird.IMGS[0]
        self.alive = True

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
        return bird_mask.overlap(top_mask, top_offset) or bird_mask.overlap(bottom_mask, bottom_offset)

# -----------------------
# Base class
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
# Helper: rotate & blit
# -----------------------
def blit_rotate_center(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect.topleft)

# -----------------------
# Draw window
# -----------------------
def draw_window(win, birds, pipes, base, score, gen=0, alive_count=0):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    base.draw(win)
    for bird in birds:
        if bird.alive:
            bird.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, (255,255,255))
    gen_text = STAT_FONT.render(f"Generation: {gen}", True, (255,255,255))
    alive_text = STAT_FONT.render(f"Alive: {alive_count}", True, (255,255,255))
    win.blit(score_text, (WIN_WIDTH - score_text.get_width() - 10, 10))
    win.blit(gen_text, (10, 10))
    win.blit(alive_text, (10, 40))
    pygame.display.update()

# -----------------------
# NEAT fitness function
# -----------------------
def eval_genomes(genomes, config):
    global GEN
    GEN += 1

    nets = []
    birds = []
    ge = []

    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run_simulation = True
    while run_simulation:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        alive_birds = [b for b in birds if b.alive]
        alive_count = len(alive_birds)
        if alive_count == 0:
            break  # end generation

        pipe_ind = 0
        if len(pipes) > 1 and alive_birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        for i, bird in enumerate(birds):
            if not bird.alive:
                continue
            bird.move()
            ge[i].fitness += 0.1
            top_dist = abs(bird.y - pipes[pipe_ind].height)
            bottom_dist = abs(bird.y - (pipes[pipe_ind].height + pipes[pipe_ind].GAP))
            output = nets[i].activate((bird.y, top_dist, bottom_dist))
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()
            for i, bird in enumerate(birds):
                if bird.alive and pipe.collide(bird):
                    bird.alive = False
                    ge[i].fitness -= 1
            if not pipe.passed and birds[0].x > pipe.x:
                pipe.passed = True
                add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH + 100))
        for r in rem:
            pipes.remove(r)

        for i, bird in enumerate(birds):
            if bird.alive and (bird.y + bird.img.get_height() >= base.y or bird.y < 0):
                bird.alive = False
                ge[i].fitness -= 1

        base.move()
        draw_window(win, birds, pipes, base, score, GEN, alive_count)

# -----------------------
# Main NEAT run
# -----------------------
def run(config_file):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genomes, 50)  # run for 50 generations
    print('\nBest genome:\n{!s}'.format(winner))

# -----------------------
# Entrypoint
# -----------------------
if __name__ == "__main__":
    GEN = 0
    pygame.init()  # Initialize all Pygame modules
    pygame.font.init()  # Ensure font module is initialized
    pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Initialize display first
    try:
        BG_IMG = pygame.transform.scale(load_image("bg.png", scale2x=False), (WIN_WIDTH, WIN_HEIGHT))
        STAT_FONT = pygame.font.SysFont("comicsans", 30)
    except Exception as e:
        print("Error loading assets.")
        print(e)
        pygame.quit()
        sys.exit(1)

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
