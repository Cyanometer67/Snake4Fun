# Author: Qirui Liu
# Date: 2024-06-02
# Contact Email: liuqirui42x@gmail.com

import pygame
import sys
import random
import os
import numpy as np

pygame.init()

# 设置屏幕大小和显示区域高度
screen_width = 640
screen_height = 640
display_height = 40
block_size = 20

# 颜色定义
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
klein_blue = (0, 47, 167)

# 设置时钟
clock = pygame.time.Clock()
screen = pygame.display.set_mode((screen_width, screen_height + display_height))

# 生成音效
def generate_sound(frequency, duration, volume, waveform='sine'):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    if waveform == 'sine':
        wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    elif waveform == 'square':
        wave = 0.5 * np.sign(np.sin(2 * np.pi * frequency * t))
    elif waveform == 'sawtooth':
        wave = 0.5 * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
    
    sound = np.int16(wave * volume * 32767)
    stereo_sound = np.column_stack((sound, sound))  # 创建双声道
    return pygame.sndarray.make_sound(stereo_sound)

# 吃食物音效 - 短促的高频音
eat_sound = generate_sound(800, 0.1, 0.5, 'sine')

# gameover音效 - 低频的递减音
gameover_sound = generate_sound(150, 0.5, 0.5, 'sawtooth')


class Snake:
    def __init__(self):
        self.body = [pygame.Rect(100, display_height + 50, block_size, block_size),
                     pygame.Rect(80, display_height + 50, block_size, block_size),
                     pygame.Rect(60, display_height + 50, block_size, block_size)]
        self.direction = 'RIGHT'
        self.change_to = self.direction

    def change_direction(self, dir):
        if dir == 'UP' and self.direction != 'DOWN':
            self.direction = 'UP'
        elif dir == 'DOWN' and self.direction != 'UP':
            self.direction = 'DOWN'
        elif dir == 'LEFT' and self.direction != 'RIGHT':
            self.direction = 'LEFT'
        elif dir == 'RIGHT' and self.direction != 'LEFT':
            self.direction = 'RIGHT'

    def move(self, wall):
        head = self.body[0].copy()
        if self.direction == 'UP':
            head.y -= block_size
        elif self.direction == 'DOWN':
            head.y += block_size
        elif self.direction == 'LEFT':
            head.x -= block_size
        elif self.direction == 'RIGHT':
            head.x += block_size

        if wall:
            if head.x < 0 or head.x >= screen_width or head.y < display_height or head.y >= screen_height + display_height:
                return False
        else:
            head.x %= screen_width
            head.y = (head.y - display_height) % screen_height + display_height

        self.body.insert(0, head)
        return True

    def grow(self):
        self.body.pop()

    def check_collision(self):
        for block in self.body[1:]:
            if self.body[0].colliderect(block):
                return True
        return False

    def draw(self):
        for rect in self.body:
            pygame.draw.rect(screen, green, rect)

class Food:
    def __init__(self):
        self.position = pygame.Rect(
            random.randrange(1, (screen_width // block_size)) * block_size,
            random.randrange(1, (screen_height // block_size)) * block_size + display_height,
            block_size, block_size)

    def spawn_food(self):
        self.position = pygame.Rect(
            random.randrange(1, (screen_width // block_size)) * block_size,
            random.randrange(1, (screen_height // block_size)) * block_size + display_height,
            block_size, block_size)

    def draw(self):
        pygame.draw.rect(screen, white, self.position)

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.high_score_wall = self.load_high_score('high_score_wall.txt')
        self.high_score_no_wall = self.load_high_score('high_score_no_wall.txt')
        self.speed = 5  # 默认速度，之后会选择
        self.speed_level = 1
        self.game_over_flag = False
        self.paused = False
        self.wall = True  # 默认有墙壁

    def reset_game(self):
        self.snake = Snake()
        self.food = Food()
        self.score = 0
        self.paused = False

    def select_speed(self):
        speed_selected = False
        speed = None
        while not speed_selected:
            screen.fill(black)
            font = pygame.font.SysFont('times new roman', 30)
            text_surface = font.render('Select Speed (1-5): ' + (str(speed) if speed else ''), True, white)
            text_rect = text_surface.get_rect()
            text_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 - 50)
            screen.blit(text_surface, text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                        speed = int(event.unicode)
                    elif event.key == pygame.K_RETURN and speed:
                        speed_selected = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        self.speed_level = speed
        return speed * 5

    def select_mode(self):
        mode_selected = False
        while not mode_selected:
            screen.fill(black)
            font = pygame.font.SysFont('times new roman', 30)
            text_surface = font.render('Select Mode: W for Wall, N for No Wall', True, white)
            text_rect = text_surface.get_rect()
            text_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 - 50)
            screen.blit(text_surface, text_rect)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.wall = True
                        mode_selected = True
                    elif event.key == pygame.K_n:
                        self.wall = False
                        mode_selected = True
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def load_high_score(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as file:
                return int(file.read())
        else:
            with open(filename, "w") as file:
                file.write("0")
            return 0

    def save_high_score(self, filename, score):
        with open(filename, "w") as file:
            file.write(str(score))

    def show_score(self, choice, color, font, size):
        score_font = pygame.font.SysFont(font, size)
        high_score = self.high_score_wall if self.wall else self.high_score_no_wall
        score_surface = score_font.render(f'Score: {self.score}  High Score: {high_score}', True, color)
        score_rect = score_surface.get_rect()
        if choice == 1:
            score_rect.topright = (screen_width - 10, 10)  # 右上角，适当的边距
        else:
            score_rect.midtop = (screen_width / 2, (screen_height + display_height) / 1.25)
        screen.blit(score_surface, score_rect)

    def show_speed_level(self, color, font, size):
        speed_font = pygame.font.SysFont(font, size)
        speed_surface = speed_font.render('Speed: ' + str(self.speed_level), True, color)
        speed_rect = speed_surface.get_rect()
        speed_rect.topleft = (10, 10)
        screen.blit(speed_surface, speed_rect)

    def game_over(self):
        high_score_filename = 'high_score_wall.txt' if self.wall else 'high_score_no_wall.txt'
        high_score = self.high_score_wall if self.wall else self.high_score_no_wall
        new_high_score = False

        if self.score > high_score:
            new_high_score = True
            if self.wall:
                self.high_score_wall = self.score
            else:
                self.high_score_no_wall = self.score
            self.save_high_score(high_score_filename, self.score)

        screen.fill(black)
        my_font = pygame.font.SysFont('times new roman', 70)
        game_over_surface = my_font.render('Game Over', True, red)
        game_over_rect = game_over_surface.get_rect()
        game_over_rect.midtop = (screen_width / 2, (screen_height + display_height) / 4)
        screen.blit(game_over_surface, game_over_rect)

        score_font = pygame.font.SysFont('times new roman', 30)
        if new_high_score:
            score_surface = score_font.render(f'Congrats! New High Score: {self.score}', True, green)
        else:
            score_surface = score_font.render(f'Your Score: {self.score}', True, red)
        score_rect = score_surface.get_rect()
        score_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 - 50)
        screen.blit(score_surface, score_rect)

        small_font = pygame.font.SysFont('times new roman', 25)
        restart_surface = small_font.render('Press R to Restart', True, white)
        restart_rect = restart_surface.get_rect()
        restart_rect.midtop = (screen_width / 2, screen_height + display_height - 50)  # Adjusted position to bottom
        screen.blit(restart_surface, restart_rect)
        
        pygame.display.flip()
        
        self.game_over_flag = True
        gameover_sound.play()  # 播放gameover音效
        while self.game_over_flag:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game_over_flag = False
                        self.main_menu()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def show_start_button(self):
        start_font = pygame.font.SysFont('times new roman', 30)
        start_surface = start_font.render('Press ', True, white)
        enter_surface = start_font.render('ENTER', True, (255, 255, 0))  # 黄色
        start_surface2 = start_font.render(' to Start', True, white)
        
        # Calculate the total width of the combined text
        total_width = start_surface.get_width() + enter_surface.get_width() + start_surface2.get_width()
        
        # Calculate the starting x position to center the combined text
        start_x = (screen_width - total_width) / 2
        start_y = (screen_height + display_height) / 2 - 50
        
        screen.fill(black)
        screen.blit(start_surface, (start_x, start_y))
        screen.blit(enter_surface, (start_x + start_surface.get_width(), start_y))
        screen.blit(start_surface2, (start_x + start_surface.get_width() + enter_surface.get_width(), start_y))
        # Add scoring rule at the bottom
        scoring_font = pygame.font.SysFont('times new roman', 20)
        scoring_surface = scoring_font.render('Scoring Rule: Each point = 10 + 2*Speed_Level', True, white)
        scoring_rect = scoring_surface.get_rect()
        scoring_rect.midtop = (screen_width / 2, screen_height + display_height - 60)
        screen.blit(scoring_surface, scoring_rect)
        
        pygame.display.flip()

    def show_restart_button(self):
        restart_font = pygame.font.SysFont('times new roman', 30)
        restart_surface = restart_font.render('Press R to Restart', True, white)
        restart_rect = restart_surface.get_rect()
        restart_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 - 50)
        screen.fill(black)
        screen.blit(restart_surface, restart_rect)
        pygame.display.flip()

    def show_pause_message(self):
        screen.fill(black)
        pause_font = pygame.font.SysFont('times new roman', 30)
        pause_surface = pause_font.render('Game Paused. Press SPACE to Resume', True, white)
        pause_rect = pause_surface.get_rect()
        pause_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 - 50)
        screen.blit(pause_surface, pause_rect)
        
        restart_surface = pause_font.render('Press R to Restart', True, white)
        restart_rect = restart_surface.get_rect()
        restart_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2)
        screen.blit(restart_surface, restart_rect)
        
        quit_surface = pause_font.render('Press Q to End the Game', True, white)
        quit_rect = quit_surface.get_rect()
        quit_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 + 50)
        screen.blit(quit_surface, quit_rect)

        speed_surface = pause_font.render('Press 1-5 to Adjust Speed', True, white)
        speed_rect = speed_surface.get_rect()
        speed_rect.midtop = (screen_width / 2, (screen_height + display_height) / 2 + 100)
        screen.blit(speed_surface, speed_rect)
        
        pygame.display.flip()

    def main_menu(self):
        self.select_mode()
        self.speed = self.select_speed()
        self.reset_game()
        self.main_game()

    def main_game(self):
        game_start = True

        while game_start:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction('UP')
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction('DOWN')
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction('LEFT')
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction('RIGHT')
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        game_start = False
                        self.main_menu()
                    elif event.key == pygame.K_q:
                        self.game_over()
                        pygame.quit()
                        sys.exit()
                    elif self.paused and event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                        self.speed_level = int(event.unicode)
                        self.speed = self.speed_level * 5
                if event.type is pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if self.paused:
                self.show_pause_message()
                continue

            if not self.snake.move(self.wall):
                self.game_over()
                game_start = False

            if self.snake.body[0].colliderect(self.food.position):
                basic_score = 10
                self.score += int(basic_score * (1 + 0.2 * self.speed_level))
                self.food.spawn_food()
                eat_sound.play()  # 播放吃食物音效
            else:
                self.snake.grow()

            if self.snake.check_collision():
                self.game_over()
                game_start = False

            screen.fill(black)
            pygame.draw.line(screen, white, (0, display_height), (screen_width, display_height))  # 画一条分隔线
            if self.wall:
                pygame.draw.line(screen, white, (0, display_height), (0, screen_height + display_height))
                pygame.draw.line(screen, white, (screen_width - 1, display_height), (screen_width - 1, screen_height + display_height))
                pygame.draw.line(screen, white, (0, screen_height + display_height - 1), (screen_width, screen_height + display_height - 1))
            self.snake.draw()
            self.food.draw()
            self.show_score(1, white, 'times new roman', 20)
            self.show_speed_level(white, 'times new roman', 20)
            pygame.display.update()
            clock.tick(self.speed)

    def main(self):
        self.show_start_button()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.main_menu()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    game = Game()
    game.main()