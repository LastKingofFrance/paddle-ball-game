import pygame
import sys
import math
import random
import os

pygame.init()

# Screen
WIDTH, HEIGHT = 500, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paddle Ball: Neon Breaker")

# Clock & Font
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 32)

# Paths
SOUND_DIR = "sounds"
HIGHSCORE_FILE = "highscore.txt"

# Load sounds
def load_sound(name):
    try:
        return pygame.mixer.Sound(os.path.join(SOUND_DIR, name))
    except:
        return pygame.mixer.Sound(buffer=b"")

bounce_sfx = load_sound("bounce.wav")
brick_sfx = load_sound("brick.wav")
powerup_sfx = load_sound("powerup.wav")
lose_sfx = load_sound("lose.wav")
win_sfx = load_sound("win.wav")

# Game constants
BALL_RADIUS = 10
POWERUP_TYPES = ["WIDE", "LIFE", "BOMB"]
POWERUP_LABELS = {"WIDE": "W", "LIFE": "+", "BOMB": "B"}
POWERUP_COLORS = {"WIDE": (0, 255, 0), "LIFE": (255, 255, 0), "BOMB": (255, 0, 0)}

# Global state
score, level, lives = 0, 1, 3
high_score = 0
game_over = False
game_win = False
game_started = False
explosive_mode = False
explosive_timer = 0

# Load and save high score
def load_high_score():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip() or "0")
    return 0

def save_high_score(new_score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(new_score))

high_score = load_high_score()

# Game setup
def create_bricks(rows):
    return [pygame.Rect(col * 70 + 25, row * 30 + 50, 60, 20)
            for row in range(rows) for col in range(7)]

def reset_ball_and_paddle():
    global paddle_x, paddle_y, ball_x, ball_y, ball_dx, ball_dy, paddle_width, paddle_speed, ball_speed
    paddle_width = max(60, 100 - (level - 1) * 10)
    paddle_speed = min(10, 7 + level // 2)
    ball_speed = min(6, 4 + int((level - 1) * 0.5))
    paddle_x = (WIDTH - paddle_width) // 2
    paddle_y = HEIGHT - 40
    ball_x = WIDTH // 2
    ball_y = HEIGHT // 2
    ball_dx = ball_speed * random.choice([-1, 1])
    ball_dy = -ball_speed

def reset_game():
    global bricks, powerups, score, level, lives, game_over, game_win, explosive_mode, explosive_timer
    score = 0
    level = 1
    lives = 3
    game_over = False
    game_win = False
    explosive_mode = False
    explosive_timer = 0
    bricks = create_bricks(5)
    powerups = []
    reset_ball_and_paddle()

def spawn_powerup(x, y):
    if random.random() < 0.25:
        kind = random.choice(POWERUP_TYPES)
        powerups.append({"x": x, "y": y, "type": kind})

def apply_powerup(pu):
    global lives, paddle_width, explosive_mode, explosive_timer
    if pu["type"] == "WIDE":
        paddle_width = min(paddle_width + 40, WIDTH)
    elif pu["type"] == "LIFE":
        lives += 1
    elif pu["type"] == "BOMB":
        explosive_mode = True
        explosive_timer = 300  # 5 seconds

def destroy_adjacent_bricks():
    global score
    removed = 0
    for b in bricks[:]:
        if abs(b.centerx - ball_x) < 80 and abs(b.centery - ball_y) < 80:
            bricks.remove(b)
            removed += 1
    if removed:
        score += removed * 5
        brick_sfx.play()

def destroy_nearby_bricks(x, y, count):
    global score
    destroyed = 0
    for b in bricks[:]:
        dist = math.hypot(b.centerx - x, b.centery - y)
        if dist < 80 and destroyed < count:
            bricks.remove(b)
            score += 5
            destroyed += 1

def draw_neon_background(tick):
    c = (50 + int(50 * math.sin(tick * 0.02)), 0, 70 + int(50 * math.cos(tick * 0.015)))
    screen.fill(c)

# Init game
reset_game()
frame = 0
running = True

while running:
    clock.tick(60)
    frame += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_high_score(high_score)
            running = False
        if event.type == pygame.KEYDOWN:
            if not game_started and event.key == pygame.K_SPACE:
                game_started = True
                reset_game()
            elif (game_over or game_win) and event.key == pygame.K_SPACE:
                reset_game()
                game_started = True

    if not game_started:
        draw_neon_background(frame)
        screen.blit(big_font.render("Paddle Ball: Neon Breaker", True, (255, 0, 255)), (70, 200))
        screen.blit(font.render("Press SPACE to start", True, (0, 255, 255)), (140, 250))
        screen.blit(font.render(f"High Score: {high_score}", True, (255, 255, 0)), (160, 280))
        pygame.display.flip()
        continue

    keys = pygame.key.get_pressed()
    if not game_over and not game_win:
        if keys[pygame.K_LEFT] and paddle_x > 0:
            paddle_x -= paddle_speed
        if keys[pygame.K_RIGHT] and paddle_x < WIDTH - paddle_width:
            paddle_x += paddle_speed

        ball_x += ball_dx
        ball_y += ball_dy

        if ball_x <= BALL_RADIUS or ball_x >= WIDTH - BALL_RADIUS:
            ball_dx *= -1
            bounce_sfx.play()
        if ball_y <= BALL_RADIUS:
            ball_dy *= -1
            bounce_sfx.play()

        paddle_rect = pygame.Rect(paddle_x, paddle_y, paddle_width, 10)
        ball_rect = pygame.Rect(ball_x - BALL_RADIUS, ball_y - BALL_RADIUS, BALL_RADIUS*2, BALL_RADIUS*2)
        if ball_rect.colliderect(paddle_rect) and ball_dy > 0:
            ball_dy *= -1
            bounce_sfx.play()

        if explosive_mode:
            explosive_timer -= 1
            if explosive_timer <= 0:
                explosive_mode = False

        for b in bricks[:]:
            if ball_rect.colliderect(b):
                bricks.remove(b)
                ball_dy *= -1
                score += 5
                spawn_powerup(b.centerx, b.centery)
                brick_sfx.play()
                if explosive_mode:
                    destroy_nearby_bricks(b.centerx, b.centery, 3)
                break

        for pu in powerups[:]:
            pu["y"] += 3
            rect = pygame.Rect(pu["x"] - 10, pu["y"] - 10, 20, 20)
            if rect.colliderect(paddle_rect):
                apply_powerup(pu)
                powerup_sfx.play()
                powerups.remove(pu)
            elif pu["y"] > HEIGHT:
                powerups.remove(pu)

        if ball_y >= HEIGHT:
            lives -= 1
            lose_sfx.play()
            if lives <= 0:
                game_over = True
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            else:
                reset_ball_and_paddle()

        if not bricks:
            level += 1
            if level > 5:
                game_win = True
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            else:
                bricks = create_bricks(4 + level)
                reset_ball_and_paddle()
                win_sfx.play()

    draw_neon_background(frame)
    pygame.draw.rect(screen, (255, 255, 255), (paddle_x, paddle_y, paddle_width, 10))
    ball_color = (255, 100, 0) if explosive_mode else (255, 0, 0)
    pygame.draw.circle(screen, ball_color, (ball_x, ball_y), BALL_RADIUS)

    for b in bricks:
        pygame.draw.rect(screen, (0, 200, 255), b)

    for pu in powerups:
        color = POWERUP_COLORS[pu["type"]]
        pygame.draw.circle(screen, color, (pu["x"], pu["y"]), 10)
        label = font.render(POWERUP_LABELS[pu["type"]], True, (0, 0, 0))
        screen.blit(label, (pu["x"] - 6, pu["y"] - 12))

    screen.blit(font.render(f"Score: {score}", True, (255,255,255)), (10, 10))
    screen.blit(font.render(f"Lives: {lives}", True, (255,255,255)), (WIDTH - 100, 10))
    screen.blit(font.render(f"Level: {level}", True, (255,255,255)), (200, 10))
    screen.blit(font.render(f"High Score: {high_score}", True, (255, 255, 0)), (150, 40))

    if explosive_mode:
        seconds_left = explosive_timer // 60
        screen.blit(font.render(f"BOMB: {seconds_left}s", True, (255, 150, 0)), (10, 40))

    if game_over:
        msg = font.render("Game Over! Press SPACE", True, (255, 255, 255))
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
    if game_win:
        msg = font.render("YOU WIN! Press SPACE", True, (0, 255, 0))
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

    pygame.display.flip()

pygame.quit()
sys.exit()
