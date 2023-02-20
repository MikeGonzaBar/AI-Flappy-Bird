from typing import List
import pygame
import neat
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(
    pygame.image.load(
        os.path.join(
            "imgs",
            "bird1.png"
        ))),
    pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]

PIPE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "pipe.png")))

BASE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "base.png")))

BG_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsasns", 50)

gen = 0


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x: int, y: int):
        """ Initializes a new instance of the Bird class.

        Args:
            x (int): The x-coordinate of the bird's starting position.
            y (int): The y-coordinate of the bird's starting position.
        """
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """ Makes the bird jump by changing its vertical velocity and resetting the tick count and height.
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """ Move the bird by updating its position and tilt angle.
        """

        # Increment the tick count to track the time since the last move
        self.tick_count += 1

        # Calculate the new height based on the bird's velocity and time
        d = self.vel*self.tick_count+1.5*self.tick_count**2

        # Cap the maximum displacement to 16 pixels
        d = min(d, 16)

        # Adjust the displacement based on the bird's direction and height
        if d < 0:
            d -= 2
        self.y = self.y + d

        # Check if the bird is diving or close to the ground
        if d < 0 or self.y < self.height + 50:
            # Increase the tilt angle to make the bird look like it's diving
            self.tilt = max(self.tilt, self.MAX_ROTATION)

        elif self.tilt > -90:  # Keep the tilt angle within the allowed range
            # Decrease the tilt angle gradually to make the bird level up
            self.tilt -= self.ROT_VEL

    def draw(self, win: pygame.Surface):
        """ Draws the bird on the window surface with rotation and animation.

        Args:
            win (pygame.Surface): The window surface to draw on.
        """
        # Increment the image count for the animation
        self.img_count += 1

        # Calculate the index of the current image based on the animation time and the number of images
        img_index = (self.img_count // self.ANIMATION_TIME) % len(self.IMGS)

        # Set the current image to the corresponding one in the list
        self.img = self.IMGS[img_index]

        # Check if the animation has reached its maximum duration
        if self.img_count >= self.ANIMATION_TIME * len(self.IMGS):
            # Reset the image count to loop the animation
            self.img_count = 0

        # If the bird is diving, show the wings in a vertical position
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            # Reset the image count to skip the animation and keep the wings in place
            self.img_count = self.ANIMATION_TIME*2

        # Rotate the current image based on the bird's tilt angle
        rotated_image = pygame.transform.rotate(self.img, self.tilt)

        # Calculate the rectangle of the rotated image with the same center as the original image
        new_rect = rotated_image.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)

        # Draw the rotated image
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self) -> pygame.Mask:
        """Returns a mask representing the bird's hitbox for pixel-perfect collision detection.

        Returns:
            pygame.mask.Mask: A mask object that can be used for collision detection.
        """
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x: int):
        """Creates a new Pipe object with the given x-coordinate.
        The height, gap, top, and bottom properties are initialized to random values.

        Args:
            x (int): The x-coordinate of the pipe.
        """
        # Initialize properties with default values
        self.x = x
        self.height = 0
        self.gap = 100
        self.top = 0
        self.bottom = 0

        # Create surfaces for the top and bottom pipes by flipping and scaling the global PIPE_IMG surface
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        # Set the passed flag to False and generate a random height for the pipe
        self.passed = False
        self.set_height()

    def set_height(self):
        """Set the height and gap of the pipe randomly.
        The height is randomly generated between 50 and 450. The top and bottom positions of the pipe
        are then calculated based on the height and the height of the top and bottom pipe images.

        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """"Moves the pipe to the left by the defined velocity.
        """
        self.x -= self.VEL

    def draw(self, win: pygame.Surface):
        """Draws the top and bottom pipes on the window at the current position.

        Args:
            win (pygame.Surface): The window surface to draw on.
        """
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird: Bird) -> bool:
        """Check if the bird collides with the pipes.

        Args:
            bird (Bird): The bird object to check collision with.

        Returns:
            bool: True if the bird collides with the pipes, False otherwise.
        """

        # Get the mask for the bird and the top/bottom pipes
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Calculate the offset of the pipes relative to the bird's position
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Check if there is any overlap between the masks of the bird and the top/bottom pipes
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        # Return True if there is any overlap, otherwise return False
        return bool(t_point or b_point)


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y: int) -> None:
        """Initialize the Base class.

        Args:
            y (int): The y-coordinate where the base will be drawn.
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Move the base to the left 
        """

        # Move both base images to the left by the specified velocity
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # If the first base image has moved off the screen to the left,
        # move it to the right of the second image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2+self.WIDTH

        # If the second base image has moved off the screen to the left,
        # move it to the right of the first image
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1+self.WIDTH

    def draw(self, win: pygame.Surface):
        """
        Draws the base image on the surface

        Args:
            win: A Pygame surface object to draw the base image onto
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win: pygame.Surface, birds: List[Bird], pipes: List[Pipe], base: Base, score: int, gen: int):
    """
    Draw the game window

    Args:
    win : pygame.Surface : the game window
    birds : List[Bird] : the list of birds
    pipes : List[Pipe] : the list of pipes
    base : Base : the base object
    score : int : the current score
    gen : int : the current generation
    """
    win.blit(BG_IMG, (0, 0))

    # Draw pipes
    for pipe in pipes:
        pipe.draw(win)

    # Draw score and generation
    text = STAT_FONT.render(f"Score {score}", 1, (255, 255, 255))
    generation = STAT_FONT.render(f"Gen {gen}", 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH-10-text.get_width(), 10))
    win.blit(generation, (10, 10))

    # Draw base
    base.draw(win)

    # Draw birds
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    """Runs a simulation of Flappy Bird game for the given set of genomes and the given configuration.

    This function takes a set of genomes and a configuration as inputs and runs a simulation of the Flappy Bird game.
    For each genome in the set, a bird is created, which is controlled by a neural network generated from the genome.
    The goal of the simulation is for the birds to fly through a series of pipes without hitting them.
    The fitness score of each genome is based on the distance the bird travels before hitting a pipe or crashing.

    Args:
        genomes (list): A list of tuples, where each tuple contains an integer ID and a genome object.
        config (neat.Config): A NEAT configuration object.
    """
    nets = []  # A list to hold the neural networks for each genome
    ge = []  # A list to hold the genomes
    birds = []  # A list to hold the birds

    global gen  # A counter for the current generation
    gen += 1

    # Create a bird and a neural network for each genome
    for _, genome in genomes:
        genome.fitness = 0  # Initialize the fitness score to zero
        # Create a neural network from the genome
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 250))  # Create a bird
        ge.append(genome)

    # Create the base and the first pipe
    base = Base(730)
    pipes = [Pipe(600)]

    # Create the window and the clock
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    # Initialize the score and the game loop
    score = 0
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # Determine which pipe each bird should look at
        pipe_ind = 0
        if birds:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False

        # Move each bird and activate its neural network to determine if it should jump
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            output = nets[x].activate((bird.y, abs(
                bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        # Add a new pipe if necessary and remove any pipes that are off screen
        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    pop_from_gen(birds, x, nets, ge)
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
                pipe.move()

        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5

            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):

            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                pop_from_gen(birds, x, nets, ge)
        if score > 50:
            break

        base.move()

        draw_window(win, birds, pipes, base, score)


def pop_from_gen(birds: List[Bird], x: int, nets: List, ge: List):
    birds.pop(x)
    nets.pop(x)
    ge.pop(x)


def run(config_path: str):
    """This function initializes the NEAT algorithm population, reports the progress to the console,
     and returns the winning genome after running the algorithm for 50 generations.

    Args:
        config_path (str): The path to the NEAT configuration file.

    Returns:
        A winning genome.
    """
    # Load configuration
    config = neat.Config(neat.DefaultGenome,
                         neat.DefaultReproduction,
                         neat.DefaultSpeciesSet,
                         neat.DefaultStagnation,
                         config_path)

    # Initialize population
    p = neat.Population(config)

    # Create console reporter and add to population
    p.add_reporter(neat.StdOutReporter(True))

    # Create statistics reporter and add to population
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Run the NEAT algorithm for 50 generations
    winner = p.run(main, 50)
    print(winner)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
