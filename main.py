import math
import multiprocessing
import os
import time
from time import sleep
import numpy.random
import pygame
import random
pygame.init()


class Fruit:
    coords = None

    def __init__(self, snake):
        Fruit.coords = (snake.rect.left, snake.rect.top)
        while snake.on_fruit():
            Fruit.coords = (
                random.randint(0, (SCREEN_WIDTH / BLOCK_SIZE) - 1) * BLOCK_SIZE,
                random.randint(0, (SCREEN_HEIGHT / BLOCK_SIZE) - 1) * BLOCK_SIZE
            )
        self.rect = pygame.Rect(Fruit.coords, (BLOCK_SIZE-2, BLOCK_SIZE-2))
        self.color = (255, 0, 0)

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)


class Brain:
    def __init__(self, n_input: int, n_hidden: int, n_output: int):
        self.w_input_hidden = numpy.random.uniform(low=-1.0, high=1.0, size=(n_hidden, n_input + 1))
        self.w_hidden_hidden = numpy.random.uniform(low=-1.0, high=1.0, size=(n_hidden, n_hidden + 1))
        self.w_hidden_output = numpy.random.uniform(low=-1.0, high=1.0, size=(n_output, n_hidden + 1))

    def serialize(self):
        return {
            'w_input_hidden': self.w_input_hidden,
            'w_hidden_hidden': self.w_hidden_hidden,
            'w_hidden_output': self.w_hidden_output,
        }

    @staticmethod
    def sigmoid(x: float):
        return 1 / (1 + pow(math.e, -x))

    @staticmethod
    def activate(n):
        return [[Brain.sigmoid(col) for col in row] for row in n]

    @staticmethod
    def mutate(vector, mutation_rate: float):
        return numpy.array([[col + random.uniform(-1.0, 1.0) if random.random() <= mutation_rate else col for col in row] for row in vector])

    @staticmethod
    def crossover(v_a, v_b):
        n_rows, n_cols = len(v_a), len(v_a[0])
        r_row, r_col = random.randint(0, n_rows), random.randint(0, n_cols)
        v_child = [[0] * n_cols for _ in range(n_rows)]

        for row in range(n_rows):
            for col in range(n_cols):
                if row < r_row or (row == r_row and col <= r_col):
                    v_child[row][col] = v_a[row][col]
                else:
                    v_child[row][col] = v_b[row][col]

        return numpy.array(v_child)

    def nn_process(self, v_input):
        # normalize, add bias to, and transpose input vector
        v_input.append(1)
        v_input = numpy.transpose(numpy.atleast_2d(v_input))
        # v_input = normalize(v_input.reshape(1, -1)).reshape(-1, 1)

        # results of layer-1 weights and input vector
        v_input_hidden = self.w_input_hidden.dot(v_input)
        v_input_hidden = self.activate(v_input_hidden)
        v_input_hidden.append([1])

        # results of layer-2 weights and layer-1 output
        v_hidden_hidden = self.w_hidden_hidden.dot(v_input_hidden)
        v_hidden_hidden = self.activate(v_hidden_hidden)
        v_hidden_hidden.append([1])

        # results of layer-3 weights and layer-2 output
        v_hidden_output = self.w_hidden_output.dot(v_hidden_hidden)
        v_hidden_output = self.activate(v_hidden_output)

        return v_hidden_output

    def decide(self, snake, fruit):
        # the 24 input nodes
        nn_inputs = []

        # calculate nn input metrics - INPUT METRIC ALGORITHM v1
        for direction in VELOCITIES:
            distance = 0
            input_fruit, input_tail, input_wall = 0, 0, 0

            # advance vision
            vision_rect = snake.rect.move(VELOCITIES[direction])
            distance += 1

            # calculate fruit distance

            # advance vision in direction to find self-collision and wall distances
            while not out_of_bounds(vision_rect):
                # snake collision
                if snake.on_self(head_coords=(vision_rect.left, vision_rect.top)):
                    input_tail = 1 / distance

                # advance
                vision_rect = vision_rect.move(VELOCITIES[direction])
                distance += 1

            # add direction input variables to input vector
            input_wall = 1 / distance
            nn_inputs.append(input_fruit)
            nn_inputs.append(input_tail)
            nn_inputs.append(input_wall)

        # process input metrics through nn and make directional decision
        nn_output = self.nn_process(nn_inputs)
        highest_node = nn_output.index(max([row[0] for row in nn_output]))
        if highest_node == 0:
            return 'west'
        elif highest_node == 1:
            return 'east'
        elif highest_node == 2:
            return 'north'
        elif highest_node == 3:
            return 'south'


class Snake:
    def __init__(self, start_coords, head_snake=None, color=None, brain=None):
        self.rect = pygame.Rect(start_coords, (BLOCK_SIZE-2, BLOCK_SIZE-2))
        self.head_snake = head_snake
        self.brain = brain
        self.color = color

        self.tail_snake = None
        self.prev_dir = None  # TODO replace this with just prev_coords
        self.prev_coords = None
        self.time_lived = 0
        self.tol = 200

        if not color:
            self.color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
        if not head_snake and not brain:
            self.brain = Brain(n_input=24, n_hidden=18, n_output=4)

    def clone(self):
        return Snake(start_coords=START_COORDS, head_snake=None, color=self.color, brain=self.brain)

    def grow(self):
        if self.tail_snake:
            # this is not the last snake; relay to next tail snake
            self.tail_snake.grow()
        else:
            # this is the last snake
            self.tail_snake = Snake(start_coords=self.prev_coords, head_snake=self, color=self.color, brain=None)

    def move(self, direction):
        if direction:
            self.prev_coords = (self.rect.left, self.rect.top)
            self.rect = self.rect.move(VELOCITIES[direction])
            if self.tail_snake:
                self.tail_snake.move(self.prev_dir)
            self.prev_dir = direction

    def print(self):
        text = "<>~"
        if self.tail_snake:
            text += self.tail_snake.print()
        if not self.head_snake:
            text = "~8~" + text
            print(text)
        return text

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        if self.tail_snake:
            self.tail_snake.draw()

    def size(self):
        if self.tail_snake:
            return 1 + self.tail_snake.size()
        return 1

    def on_self(self, head_coords=None):
        if not head_coords:
            head_coords = (self.rect.left, self.rect.top)
        if self.tail_snake:
            tail_coords = (self.tail_snake.rect.left, self.tail_snake.rect.top)
            return (head_coords == tail_coords) or self.tail_snake.on_self(head_coords=head_coords)
        return False

    def on_fruit(self):
        fruit_coords = (Fruit.coords[0], Fruit.coords[1])
        snake_coords = (self.rect.left, self.rect.top)
        if self.tail_snake:
            return snake_coords == fruit_coords or self.tail_snake.on_fruit()
        return snake_coords == fruit_coords

    def fitness(self):
        return ((self.size() - 1) * 200) + (self.time_lived % 201)

    def breed(self, partner_snake):
        # random color
        child_color = random.choice([self.color, partner_snake.color])
        child_color = ((child_color[0] + random.randint(-1, 1)) % 256,
                       (child_color[1] + random.randint(-1, 1)) % 256,
                       (child_color[2] + random.randint(-1, 1)) % 256)

        # crossed brain
        child_brain = Brain(0, 0, 0)
        child_brain.w_input_hidden = Brain.crossover(v_a=self.brain.w_input_hidden, v_b=partner_snake.brain.w_input_hidden)
        child_brain.w_hidden_hidden = Brain.crossover(v_a=self.brain.w_hidden_hidden, v_b=partner_snake.brain.w_hidden_hidden)
        child_brain.w_hidden_output = Brain.crossover(v_a=self.brain.w_hidden_output, v_b=partner_snake.brain.w_hidden_output)

        # mutate brain
        child_brain.w_input_hidden = Brain.mutate(mutation_rate=MUTATION_RATE, vector=child_brain.w_input_hidden)
        child_brain.w_hidden_hidden = Brain.mutate(mutation_rate=MUTATION_RATE, vector=child_brain.w_hidden_hidden)
        child_brain.w_hidden_output = Brain.mutate(mutation_rate=MUTATION_RATE, vector=child_brain.w_hidden_output)

        # create snake
        child_snake = Snake(start_coords=START_COORDS, head_snake=None, color=child_color, brain=child_brain)

        return child_snake


def block_distance(rect1, rect2) -> int:
    return int(abs(rect1.left - rect2.left) + abs(rect1.top - rect2.top))


def update_display(snake, fruit, fps):
    screen.fill(COLOR_BLACK)
    snake.draw()
    fruit.draw()
    pygame.display.flip()
    sleep(1/fps)


def out_of_bounds(rect):
    return rect.left < 0 or rect.left >= SCREEN_WIDTH or rect.top < 0 or rect.top >= SCREEN_HEIGHT


def play_game(p_snake) -> Snake:
    # initial game fruit
    fruit = Fruit(snake=p_snake)

    # draw & display initial frame
    if SHOW_GRAPHICS:
        update_display(snake=p_snake, fruit=fruit, fps=0.5)

    # play while snake is alive
    while p_snake.tol > 0:
        # move snake
        p_snake.move(direction=p_snake.brain.decide(snake=p_snake, fruit=fruit))  # TODO rework this

        # did the snake eat the fruit?
        if p_snake.on_fruit():
            p_snake.grow()
            fruit = Fruit(snake=p_snake)
            p_snake.tol += 100

        # did the snake collide with itself?
        if p_snake.on_self() or out_of_bounds(p_snake.rect):
            break

        # draw & display current frame
        if SHOW_GRAPHICS:
            update_display(snake=p_snake, fruit=fruit, fps=0.8)

        # advance frame
        p_snake.time_lived += 1
        p_snake.tol -= 1

    return p_snake


# game constants
COLOR_BLACK = 0, 0, 0
COLOR_WHITE = 255, 255, 255
BLOCK_SIZE = 30
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 600, 600
SHOW_GRAPHICS = True
START_COORDS = (BLOCK_SIZE * 0, BLOCK_SIZE * 0)
VELOCITIES = {
    'west': [-BLOCK_SIZE, 0],
    'east': [BLOCK_SIZE, 0],
    'north': [0, -BLOCK_SIZE],
    'south': [0, BLOCK_SIZE],
    'north-west': [-BLOCK_SIZE, -BLOCK_SIZE],
    'north-east': [BLOCK_SIZE, -BLOCK_SIZE],
    'south-west': [-BLOCK_SIZE, BLOCK_SIZE],
    'south-east': [BLOCK_SIZE, BLOCK_SIZE],
}
if SHOW_GRAPHICS:
    screen = pygame.display.set_mode(SCREEN_SIZE)

# world constants
POPULATION_SIZE = 3000
MUTATION_RATE = 0.01
BREEDING_THRESHOLD = 0.05
MAX_GENERATIONS = 25
BLUEPRINT_SNAKE_ID = 59857

# world vars
_id = random.randint(10000, 99999)
generation = 0
gen_data = {
    0: {
        'gen_fitness': 0,
        'gen_fitness_roc': 0,
        'alpha_fitness': 0,
        'alpha_size': 0,
        'alpha_genetics': None,
    }
}

# create initial snake generation
if BLUEPRINT_SNAKE_ID:
    blueprint_brain = Brain(0, 0, 0)
    blueprint_brain.w_input_hidden = numpy.loadtxt('snake_data/{}/w_input_hidden.txt'.format(BLUEPRINT_SNAKE_ID))
    blueprint_brain.w_hidden_hidden = numpy.loadtxt('snake_data/{}/w_hidden_hidden.txt'.format(BLUEPRINT_SNAKE_ID))
    blueprint_brain.w_hidden_output = numpy.loadtxt('snake_data/{}/w_hidden_output.txt'.format(BLUEPRINT_SNAKE_ID))
    blueprint_snake = Snake(start_coords=START_COORDS, head_snake=None, brain=blueprint_brain)

    if SHOW_GRAPHICS:
        play_game(p_snake=blueprint_snake)
        exit(0)

    snakes = [blueprint_snake.breed(blueprint_snake) for _ in range(POPULATION_SIZE)]
else:
    # use completely randomized snakes
    snakes = [Snake(start_coords=START_COORDS, head_snake=None) for _ in range(POPULATION_SIZE)]

# begin world game
print("\n-- World begin --")
while generation < MAX_GENERATIONS:
    # new generation
    generation += 1
    start_time = time.time()
    print("Generation: {}".format(generation))

    # test the fitness of each snake in the generation
    with multiprocessing.Pool() as pool:
        snakes = pool.map(play_game, snakes)
    completion_time = round(time.time() - start_time, 2)
    print("Fitness testing completed in {} seconds".format(completion_time))

    # sort snakes by fitness
    fittest_snakes = sorted({snake: snake.fitness() for snake in snakes}.items(), key=lambda kv: kv[1], reverse=True)[:math.floor(POPULATION_SIZE * BREEDING_THRESHOLD)]
    alpha_snake = fittest_snakes[0][0]

    # analyze generation results
    gen_fitness = round(sum([snake.fitness() for snake in snakes]) / POPULATION_SIZE, 2)
    gen_fitness_roc = round(gen_fitness - gen_data[generation - 1]['gen_fitness'], 2)

    # breed the next gen of snakes - BREEDING ALGORITHM v2
    # (1 alpha clone + 5.0% alpha-alpha pairs + 95.0% random fit snake pairs)
    alpha_clones = [alpha_snake.clone()] + [alpha_snake.breed(alpha_snake) for _ in range(math.floor(POPULATION_SIZE * 0.05))]
    snakes = alpha_clones + [random.choice(fittest_snakes)[0].breed(random.choice(fittest_snakes)[0]) for _ in range(POPULATION_SIZE - len(alpha_clones))]

    # store & log generation results
    gen_data[generation] = {
        'gen_fitness': gen_fitness,
        'gen_fitness_roc': gen_fitness_roc,
        'alpha_fitness': alpha_snake.fitness(),
        'alpha_size': alpha_snake.size(),
        'alpha_genetics': alpha_snake.brain.serialize(),
    }
    print("Gen: fitness={}, fitness ROC={}".format(gen_fitness, gen_fitness_roc))
    print("Alpha: fitness={}, size={}, color={}".format(
        alpha_snake.fitness(), alpha_snake.size(), alpha_snake.color
    ))
    print()

# analyze world multi-generational results
world_fitness = round(sum([gen_data[i]['gen_fitness'] for i in range(1, MAX_GENERATIONS + 1)]) / MAX_GENERATIONS, 2)
world_fitness_roc = round(sum([gen_data[i]['gen_fitness_roc'] for i in range(1, MAX_GENERATIONS + 1)]) / MAX_GENERATIONS, 2)
sigma_gen = sorted(gen_data.items(), key=lambda kv: kv[1]['alpha_fitness'], reverse=True)[0]

# report results
print("-- World complete --")
print("Parameters: id={}, max generations={}, population size={}, mutation rate={}, breeding threshold={}, blueprint snake={}".format(
    _id, MAX_GENERATIONS, POPULATION_SIZE, MUTATION_RATE, BREEDING_THRESHOLD, BLUEPRINT_SNAKE_ID
))
print("World: fitness={}, fitness ROC={}".format(world_fitness, world_fitness_roc))
print("Sigma: generation={}, fitness={}, size={}".format(
    sigma_gen[0], sigma_gen[1]['alpha_fitness'], sigma_gen[1]['alpha_size']
))

# save results
os.mkdir("snake_data/{}/".format(_id))
for w_layer in sigma_gen[1]['alpha_genetics']:
    v_weights = sigma_gen[1]['alpha_genetics'][w_layer]
    numpy.savetxt("snake_data/{}/{}.txt".format(_id, w_layer), v_weights)
print("Sigma genetics saved to 'snake_data/{}/'.".format(_id))
