import sys
from time import sleep
import pygame
import random
pygame.init()


class Snake:
    def __init__(self, start_coords, prev_snake, next_dir):
        self.rect = pygame.Rect(start_coords, (BLOCK_SIZE, BLOCK_SIZE))
        self.color = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
        self.next_dir = next_dir
        self.prev_snake = prev_snake
        self.next_snake = None


# constants
COLOR_BLACK = 0, 0, 0
COLOR_WHITE = 255, 255, 255
BLOCK_SIZE = 30
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 600, 600
START_COORDS = (BLOCK_SIZE * 6, BLOCK_SIZE * 5)
VELOCITIES = {
    'west': [BLOCK_SIZE, 0],
    'east': [-BLOCK_SIZE, 0],
    'north': [0, -BLOCK_SIZE],
    'south': [0, BLOCK_SIZE],
    'north-west': [BLOCK_SIZE, -BLOCK_SIZE],
    'north-east': [-BLOCK_SIZE, -BLOCK_SIZE],
    'south-west': [BLOCK_SIZE, BLOCK_SIZE],
    'south-east': [-BLOCK_SIZE, BLOCK_SIZE],
}

# game vars
frame = 0
screen = pygame.display.set_mode(SCREEN_SIZE)
snake = Snake(start_coords=START_COORDS, prev_snake=None, next_dir='south-west')

# play
while frame < 1000:
    print("Frame: {} | Next direction: {} | Coords: ({}, {}, {}, {})".format(
        frame, snake.next_dir, snake.rect.left, snake.rect.right, snake.rect.top, snake.rect.bottom)
    )

    # draw & display current frame
    screen.fill(COLOR_BLACK)
    pygame.draw.rect(screen, snake.color, snake.rect)
    pygame.display.flip()

    # event listeners
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    # move snake
    snake.rect = snake.rect.move(VELOCITIES[snake.next_dir])

    # decide next direction
    if snake.rect.left <= 0:
        snake.next_dir = random.choice(['south-west', 'north-west', 'west'])
    if snake.rect.right >= SCREEN_WIDTH:
        snake.next_dir = random.choice(['south-east', 'north-east', 'east'])
    if snake.rect.top <= 0:
        snake.next_dir = random.choice(['south-west', 'south-east', 'south'])
    if snake.rect.bottom >= SCREEN_HEIGHT:
        snake.next_dir = random.choice(['north-west', 'north-east', 'north'])

    # advance frame
    frame += 1
    sleep(1/10)

