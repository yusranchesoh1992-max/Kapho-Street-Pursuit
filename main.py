import pygame
import random
import math
import sys

# ============================================================
# Kapho Street Pursuit
# เกมแข่งรถกะพ้อไล่ล่า - เวอร์ชันอัปเกรด
# Python 3 + Pygame
# ============================================================

pygame.init()
pygame.mixer.quit()  # ให้เกมทำงานได้แม้ไม่มีระบบเสียง

BASE_WIDTH, BASE_HEIGHT = 900, 650

# Android/mobile-friendly display:
# The game logic keeps a 900x650 virtual canvas and scales it to the real screen.
display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
DISPLAY_WIDTH, DISPLAY_HEIGHT = display.get_size()
WIDTH, HEIGHT = BASE_WIDTH, BASE_HEIGHT
screen = pygame.Surface((WIDTH, HEIGHT))
pygame.display.set_caption("Kapho Street Pursuit")
clock = pygame.time.Clock()

# -------------------- Colors --------------------
GREEN = (32, 115, 48)
DARK_GREEN = (20, 80, 32)
ROAD = (55, 55, 60)
ROAD_EDGE = (120, 95, 55)
WHITE = (245, 245, 245)
BLACK = (15, 15, 15)
BLUE = (35, 110, 230)
LIGHT_BLUE = (90, 180, 255)
ORANGE = (255, 140, 20)
RED = (210, 35, 35)
YELLOW = (255, 220, 50)
GRAY = (150, 150, 155)
DARK_GRAY = (35, 35, 40)

# -------------------- Road --------------------
ROAD_LEFT = 190
ROAD_RIGHT = 710
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
LANES = 3
LANE_WIDTH = ROAD_WIDTH // LANES
LANE_CENTERS = [
    ROAD_LEFT + LANE_WIDTH // 2,
    ROAD_LEFT + LANE_WIDTH + LANE_WIDTH // 2,
    ROAD_LEFT + 2 * LANE_WIDTH + LANE_WIDTH // 2,
]

# -------------------- Fonts --------------------
def make_font(size, bold=False):
    # พยายามใช้ฟอนต์ที่รองรับภาษาไทย
    candidates = [
        "Noto Sans Thai",
        "Tahoma",
        "Arial",
        "DejaVu Sans",
    ]
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)

font_small = make_font(22)
font = make_font(28, True)
font_big = make_font(54, True)
font_title = make_font(64, True)

# -------------------- Game State --------------------
MENU = "menu"
PLAYING = "playing"
GAME_OVER = "game_over"

state = MENU
score = 0
distance = 0.0
speed = 7.0
max_speed = 15.0
health = 100
pursuit_distance = 180.0

player_w, player_h = 48, 82
player_x = WIDTH // 2 - player_w // 2
player_y = HEIGHT - 145
player_speed = 8.0

obstacles = []
spawn_timer = 0
road_scroll = 0

particles = []
shake_timer = 0

# -------------------- Mobile Touch Controls --------------------
# These buttons are drawn on the virtual 900x650 canvas and work with
# both touch events and mouse events (useful for testing on a PC).
touch_left = False
touch_right = False

LEFT_BUTTON = pygame.Rect(35, HEIGHT - 115, 120, 80)
RIGHT_BUTTON = pygame.Rect(WIDTH - 155, HEIGHT - 115, 120, 80)

def update_touch_controls(pos, pressed):
    global touch_left, touch_right
    x, y = pos
    touch_left = pressed and LEFT_BUTTON.collidepoint(x, y)
    touch_right = pressed and RIGHT_BUTTON.collidepoint(x, y)

def screen_to_game(pos):
    x, y = pos
    sx = WIDTH / DISPLAY_WIDTH
    sy = HEIGHT / DISPLAY_HEIGHT
    return (int(x * sx), int(y * sy))

def draw_mobile_controls():
    # Large translucent controls designed for thumbs.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rounded_rect(overlay, (20, 20, 20, 150), LEFT_BUTTON, 18)
    pygame.draw.rounded_rect(overlay, (20, 20, 20, 150), RIGHT_BUTTON, 18)
    pygame.draw.polygon(
        overlay, WHITE,
        [(LEFT_BUTTON.centerx + 22, LEFT_BUTTON.centery - 22),
         (LEFT_BUTTON.centerx - 22, LEFT_BUTTON.centery),
         (LEFT_BUTTON.centerx + 22, LEFT_BUTTON.centery + 22)]
    )
    pygame.draw.polygon(
        overlay, WHITE,
        [(RIGHT_BUTTON.centerx - 22, RIGHT_BUTTON.centery - 22),
         (RIGHT_BUTTON.centerx + 22, RIGHT_BUTTON.centery),
         (RIGHT_BUTTON.centerx - 22, RIGHT_BUTTON.centery + 22)]
    )
    screen.blit(overlay, (0, 0))

def present():
    # Scale the virtual game canvas to the real phone display.
    scaled = pygame.transform.smoothscale(screen, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
    display.blit(scaled, (0, 0))
    pygame.display.flip()

# -------------------- Helpers --------------------
def reset_game():
    global score, distance, speed, health, pursuit_distance
    global player_x, player_y, obstacles, spawn_timer
    global road_scroll, particles, shake_timer

    score = 0
    distance = 0.0
    speed = 7.0
    health = 100
    pursuit_distance = 180.0

    player_x = WIDTH // 2 - player_w // 2
    player_y = HEIGHT - 145

    obstacles = []
    spawn_timer = 0
    road_scroll = 0
    particles = []
    shake_timer = 0


def draw_text(text, pos, color=WHITE, fnt=font, center=False):
    img = fnt.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(img, rect)


def spawn_particle(x, y, color):
    particles.append({
        "x": x,
        "y": y,
        "vx": random.uniform(-3, 3),
        "vy": random.uniform(-4, 1),
        "life": random.randint(18, 35),
        "color": color,
        "size": random.randint(2, 5),
    })


def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.15
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)


def draw_particles():
    for p in particles:
        pygame.draw.circle(
            screen,
            p["color"],
            (int(p["x"]), int(p["y"])),
            p["size"]
        )


# -------------------- Background --------------------
def draw_tree(x, y, scale=1.0):
    trunk_w = max(5, int(10 * scale))
    trunk_h = max(15, int(38 * scale))
    pygame.draw.rect(
        screen, (105, 65, 30),
        (int(x - trunk_w / 2), int(y), trunk_w, trunk_h)
    )
    r = int(25 * scale)
    pygame.draw.circle(screen, DARK_GREEN, (int(x), int(y)), r)
    pygame.draw.circle(screen, GREEN, (int(x - r * 0.7), int(y + 3)), r)
    pygame.draw.circle(screen, GREEN, (int(x + r * 0.7), int(y + 4)), r)


def draw_background():
    screen.fill(GREEN)

    # สองข้างทาง
    for x in range(30, ROAD_LEFT - 25, 75):
        y = 90 + ((x * 37) % 210)
        draw_tree(x, y, 0.8)

    for x in range(ROAD_RIGHT + 35, WIDTH - 20, 75):
        y = 70 + ((x * 29) % 240)
        draw_tree(x, y, 0.85)

    # เส้นขอบไหล่ทาง
    pygame.draw.rect(
        screen, ROAD_EDGE,
        (ROAD_LEFT - 15, 0, 15, HEIGHT)
    )
    pygame.draw.rect(
        screen, ROAD_EDGE,
        (ROAD_RIGHT, 0, 15, HEIGHT)
    )

    # ถนน
    pygame.draw.rect(
        screen, ROAD,
        (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT)
    )

    # เส้นเลนเคลื่อนที่
    dash_h = 55
    gap = 35
    offset = road_scroll % (dash_h + gap)

    for lane in range(1, LANES):
        x = ROAD_LEFT + lane * LANE_WIDTH
        for y in range(-dash_h, HEIGHT + dash_h, dash_h + gap):
            pygame.draw.rect(
                screen,
                WHITE,
                (x - 3, y + offset, 6, dash_h)
            )

    # เส้นขอบถนน
    pygame.draw.line(
        screen, WHITE,
        (ROAD_LEFT, 0),
        (ROAD_LEFT, HEIGHT),
        5
    )
    pygame.draw.line(
        screen, WHITE,
        (ROAD_RIGHT, 0),
        (ROAD_RIGHT, HEIGHT),
        5
    )


# -------------------- Cars --------------------
def draw_player_car(x, y):
    # เงา
    pygame.draw.ellipse(
        screen, (20, 20, 20),
        (x - 3, y + 8, player_w + 6, player_h + 82)
    )

    # ตัวรถ
    pygame.draw.rounded_rect(
        screen,
        BLUE,
        (x, y, player_w, player_h),
        12
    )

    # หลังคา/กระจก
    pygame.draw.polygon(
        screen,
        LIGHT_BLUE,
        [
            (x + 9, y + 22),
            (x + 15, y + 9),
            (x + 33, y + 9),
            (x + 40, y + 22),
            (x + 37, y + 48),
            (x + 11, y + 48),
        ]
    )

    # กระจกกลาง
    pygame.draw.line(
        screen, BLUE,
        (x + 12, y + 35),
        (x + 36, y + 35),
        3
    )

    # ไฟหน้า
    pygame.draw.rect(screen, YELLOW, (x + 6, y + 4, 10, 6), border_radius=2)
    pygame.draw.rect(screen, YELLOW, (x + 32, y + 4, 10, 6), border_radius=2)

    # ไฟท้าย
    pygame.draw.rect(screen, RED, (x + 6, y + 70, 10, 7), border_radius=2)
    pygame.draw.rect(screen, RED, (x + 32, y + 70, 10, 7), border_radius=2)

    # ล้อ
    for wx in (x - 5, x + player_w - 1):
        pygame.draw.rect(
            screen, BLACK,
            (wx, y + 16, 7, 19),
            border_radius=3
        )
        pygame.draw.rect(
            screen, BLACK,
            (wx, y + 53, 7, 19),
            border_radius=3
        )


def draw_pursuit_car(x, y, scale=1.0):
    w = int(55 * scale)
    h = int(90 * scale)

    # แสงไซเรน
    pygame.draw.circle(
        screen, RED,
        (int(x + w * 0.32), int(y + 8)),
        max(3, int(5 * scale))
    )
    pygame.draw.circle(
        screen, LIGHT_BLUE,
        (int(x + w * 0.68), int(y + 8)),
        max(3, int(5 * scale))
    )

    pygame.draw.rounded_rect(
        screen,
        ORANGE,
        (int(x), int(y), w, h),
        max(5, int(10 * scale))
    )

    pygame.draw.polygon(
        screen,
        (80, 160, 210),
        [
            (int(x + 10 * scale), int(y + 26 * scale)),
            (int(x + 17 * scale), int(y + 12 * scale)),
            (int(x + 38 * scale), int(y + 12 * scale)),
            (int(x + 45 * scale), int(y + 26 * scale)),
            (int(x + 42 * scale), int(y + 48 * scale)),
            (int(x + 13 * scale), int(y + 48 * scale)),
        ]
    )

    pygame.draw.rect(
        screen, WHITE,
        (int(x + 7 * scale), int(y + 3 * scale),
         int(41 * scale), max(2, int(5 * scale))),
        border_radius=2
    )

    pygame.draw.rect(
        screen, BLACK,
        (int(x - 4 * scale), int(y + 20 * scale),
         max(3, int(6 * scale)), int(22 * scale)),
        border_radius=2
    )
    pygame.draw.rect(
        screen, BLACK,
        (int(x + w - 2 * scale), int(y + 20 * scale),
         max(3, int(6 * scale)), int(22 * scale)),
        border_radius=2
    )


# -------------------- Obstacles --------------------
def spawn_obstacle():
    lane = random.randrange(LANES)
    x = LANE_CENTERS[lane] - 25

    kind = random.choice(["rock", "barrier", "cone"])
    obstacles.append({
        "rect": pygame.Rect(x, -80, 50, 50),
        "kind": kind,
        "speed": random.uniform(0.9, 1.15),
    })


def draw_obstacle(obs):
    r = obs["rect"]
    kind = obs["kind"]

    if kind == "rock":
        pygame.draw.polygon(
            screen,
            (95, 75, 65),
            [
                (r.left + 3, r.bottom),
                (r.left + 10, r.top + 12),
                (r.left + 25, r.top),
                (r.right - 5, r.top + 14),
                (r.right - 2, r.bottom),
            ]
        )
        pygame.draw.circle(
            screen, (135, 110, 90),
            (r.centerx - 5, r.centery - 8), 6
        )

    elif kind == "barrier":
        pygame.draw.rect(screen, RED, r, border_radius=5)
        for i in range(0, 50, 14):
            pygame.draw.line(
                screen, WHITE,
                (r.left + i, r.bottom),
                (r.left + i + 12, r.top),
                5
            )

    else:
        pygame.draw.polygon(
            screen,
            ORANGE,
            [
                (r.centerx, r.top),
                (r.left + 5, r.bottom),
                (r.right - 5, r.bottom),
            ]
        )
        pygame.draw.rect(
            screen, WHITE,
            (r.left + 12, r.top + 28, 26, 6)
        )


# -------------------- HUD --------------------
def draw_hud():
    # กล่องข้อมูล
    pygame.draw.rounded_rect(
        screen, (0, 0, 0, 150),
        (15, 15, 315, 135),
        15
    )

    draw_text(f"ระยะทาง: {int(distance)} m", (30, 25), WHITE, font)
    draw_text(f"ความเร็ว: {int(speed * 15)} km/h", (30, 58), WHITE, font_small)

    # HP
    draw_text("รถ:", (30, 91), WHITE, font_small)
    pygame.draw.rect(screen, DARK_GRAY, (78, 96, 220, 20), border_radius=8)
    pygame.draw.rect(
        screen,
        RED if health < 35 else YELLOW,
        (78, 96, int(220 * health / 100), 20),
        border_radius=8
    )

    # ระยะรถไล่ล่า
    box_x = WIDTH - 310
    pygame.draw.rounded_rect(
        screen, (0, 0, 0, 150),
        (box_x, 15, 295, 75),
        15
    )
    draw_text(
        f"ผู้ไล่ล่า: {int(pursuit_distance)} m",
        (box_x + 15, 25),
        ORANGE,
        font_small
    )

    bar_x = box_x + 15
    bar_y = 58
    pygame.draw.rect(
        screen, DARK_GRAY,
        (bar_x, bar_y, 265, 13),
        border_radius=6
    )
    fill = max(0, min(265, int(265 * pursuit_distance / 180)))
    pygame.draw.rect(
        screen,
        ORANGE,
        (bar_x, bar_y, fill, 13),
        border_radius=6
    )


# -------------------- Menu --------------------
def draw_menu():
    draw_background()

    # Overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 115))
    screen.blit(overlay, (0, 0))

    draw_text(
        "KAPHO STREET",
        (WIDTH // 2, 155),
        YELLOW,
        font_title,
        True
    )
    draw_text(
        "PURSUIT",
        (WIDTH // 2, 220),
        ORANGE,
        font_big,
        True
    )

    draw_pursuit_car(WIDTH // 2 - 120, 285, 1.3)
    draw_player_car(WIDTH // 2 + 55, 285)

    pygame.draw.rounded_rect(
        screen, BLUE,
        (WIDTH // 2 - 150, 470, 300, 65),
        15
    )
    draw_text(
        "กด SPACE เพื่อเริ่มเกม",
        (WIDTH // 2, 503),
        WHITE,
        font,
        True
    )

    draw_text(
        "← → หรือ A / D : บังคับรถ",
        (WIDTH // 2, 565),
        WHITE,
        font_small,
        True
    )


# -------------------- Game Over --------------------
def draw_game_over():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    draw_text(
        "GAME OVER",
        (WIDTH // 2, 180),
        RED,
        font_title,
        True
    )

    draw_text(
        "รถไล่ล่าตามทันแล้ว!",
        (WIDTH // 2, 255),
        WHITE,
        font,
        True
    )

    draw_text(
        f"ระยะทางที่ทำได้: {int(distance)} m",
        (WIDTH // 2, 310),
        YELLOW,
        font,
        True
    )

    draw_text(
        f"คะแนน: {score}",
        (WIDTH // 2, 350),
        WHITE,
        font,
        True
    )

    pygame.draw.rounded_rect(
        screen, BLUE,
        (WIDTH // 2 - 180, 425, 360, 60),
        15
    )
    draw_text(
        "SPACE = เล่นใหม่    ESC = ออก",
        (WIDTH // 2, 455),
        WHITE,
        font_small,
        True
    )


# -------------------- Main Game --------------------
running = True

while running:
    dt = clock.tick(60) / 1000.0

    # -------- Events --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = screen_to_game(event.pos)
            if state == MENU and event.button == 1:
                reset_game()
                state = PLAYING
            elif state == GAME_OVER and event.button == 1:
                reset_game()
                state = PLAYING
            elif state == PLAYING:
                update_touch_controls(pos, True)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                touch_left = False
                touch_right = False

        elif event.type == pygame.FINGERDOWN:
            pos = screen_to_game((event.x * DISPLAY_WIDTH, event.y * DISPLAY_HEIGHT))
            if state == MENU:
                reset_game()
                state = PLAYING
            elif state == GAME_OVER:
                reset_game()
                state = PLAYING
            else:
                update_touch_controls(pos, True)

        elif event.type == pygame.FINGERUP:
            touch_left = False
            touch_right = False

        if event.type == pygame.KEYDOWN:
            if state == MENU and event.key == pygame.K_SPACE:
                reset_game()
                state = PLAYING

            elif state == GAME_OVER:
                if event.key == pygame.K_SPACE:
                    reset_game()
                    state = PLAYING
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif state == PLAYING and event.key == pygame.K_ESCAPE:
                state = MENU

    # -------- Menu --------
    if state == MENU:
        draw_menu()
        present()
        continue

    # -------- Game Over --------
    if state == GAME_OVER:
        draw_background()
        draw_particles()
        draw_game_over()
        present()
        continue

    # -------- Controls --------
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT] or keys[pygame.K_a] or touch_left:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d] or touch_right:
        player_x += player_speed

    player_x = max(
        ROAD_LEFT + 10,
        min(player_x, ROAD_RIGHT - player_w - 10)
    )

    # เร่งความเร็วตามระยะทาง
    speed = min(max_speed, 7.0 + distance / 500)

    # ถนนเคลื่อนที่
    road_scroll += int(speed * 2)

    # ระยะทาง
    distance += speed * dt * 1.8
    score = int(distance * 10)

    # -------- Spawn --------
    spawn_timer += 1

    spawn_interval = max(24, int(58 - speed * 2))

    if spawn_timer >= spawn_interval:
        spawn_obstacle()
        spawn_timer = 0

        # เมื่อเร็วขึ้น มีโอกาสสร้างอุปสรรคเพิ่ม
        if speed > 11 and random.random() < 0.18:
            spawn_obstacle()

    # -------- Move Obstacles --------
    player_rect = pygame.Rect(
        int(player_x), int(player_y),
        player_w, player_h
    )

    for obs in obstacles[:]:
        obs["rect"].y += int(speed * obs["speed"])

        if obs["rect"].top > HEIGHT:
            obstacles.remove(obs)

    # -------- Collision --------
    for obs in obstacles[:]:
        if player_rect.colliderect(obs["rect"]):
            obstacles.remove(obs)

            health -= 25
            pursuit_distance -= 45

            shake_timer = 12

            for _ in range(18):
                spawn_particle(
                    player_x + player_w // 2,
                    player_y + player_h // 2,
                    random.choice([RED, ORANGE, YELLOW, WHITE])
                )

            speed = max(6, speed - 1.2)

    # -------- Pursuit Logic --------
    # รถไล่ล่าจะค่อย ๆ เข้าใกล้เมื่อเกมเร็วขึ้น
    pursuit_distance -= 0.018 * speed

    # ถ้าขับดีและไม่ชน จะค่อย ๆ สร้างระยะห่างกลับ
    if len(obstacles) < 4:
        pursuit_distance += 0.025

    pursuit_distance = min(180, pursuit_distance)

    # -------- Particles --------
    update_particles()

    # ควันจากรถ
    if random.random() < 0.45:
        spawn_particle(
            player_x + player_w // 2 + random.randint(-8, 8),
            player_y + player_h + 4,
            (190, 190, 190)
        )

    # -------- Lose Conditions --------
    if health <= 0 or pursuit_distance <= 0:
        state = GAME_OVER

    # -------- Drawing --------
    draw_background()

    # อุปสรรค
    for obs in obstacles:
        draw_obstacle(obs)

    # รถไล่ล่า: ตำแหน่งสัมพันธ์กับระยะห่าง
    chase_scale = 0.8
    chase_y = HEIGHT - 35 - min(210, pursuit_distance * 0.95)
    chase_x = WIDTH // 2 - int(27 * chase_scale)
    draw_pursuit_car(chase_x, chase_y, chase_scale)

    # รถผู้เล่น
    draw_player_car(int(player_x), player_y)

    # เอฟเฟกต์
    draw_particles()

    draw_hud()
    draw_mobile_controls()

    # แจ้งเตือนเมื่อรถไล่ล่าใกล้
    if pursuit_distance < 60:
        draw_text(
            "ระวัง! รถไล่ล่าใกล้เข้ามาแล้ว!",
            (WIDTH // 2, 115),
            RED,
            font,
            True
        )

    # Screen shake
    if shake_timer > 0:
        shake_timer -= 1

    present()

pygame.quit()
sys.exit()
