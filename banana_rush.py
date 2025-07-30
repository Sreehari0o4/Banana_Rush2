import cv2
import mediapipe as mp
import pygame
import random
import math
import sys

# Initialize MediaPipe Hand
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# Helper to check if index finger is up (extended)
def is_index_finger_up(landmarks):
    return landmarks[8].y < landmarks[6].y and abs(landmarks[8].x - landmarks[6].x) < 0.1

# Helper to check if all fingers are folded (for pause)
def is_hand_closed(landmarks):
    return all(landmarks[i].y > landmarks[i-2].y for i in [8, 12, 16, 20])

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Banana Rush')
clock = pygame.time.Clock()

# Load assets (placeholder colors)
BANANA_COLOR = (255, 255, 0)
COCONUT_COLOR = (139, 69, 19)
BOMB_COLOR = (0, 0, 0)
BG_COLOR = (34, 139, 34)

font = pygame.font.SysFont('comicsans', 36)

# Game variables
score = 0
object_speed = 3
spawn_rate = 30
objects = []
frame_count = 0
lives = 3
selected_difficulty = None

# Game state
game_state = 'menu'

def draw_menu(paused=False):
    screen.fill((20, 40, 20))
    title = font.render('Banana Rush', True, (255, 255, 0))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))

    easy_text = font.render('1: Easy', True, (200, 255, 200))
    screen.blit(easy_text, (WIDTH//2 - easy_text.get_width()//2, 150))
    med_text = font.render('2: Medium', True, (255, 200, 200))
    screen.blit(med_text, (WIDTH//2 - med_text.get_width()//2, 200))
    hard_text = font.render('3: Hard', True, (255, 100, 100))
    screen.blit(hard_text, (WIDTH//2 - hard_text.get_width()//2, 250))

    if selected_difficulty:
        start_text = font.render('S: Start Game', True, (255, 255, 255))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, 320))

    quit_text = font.render('Q: Quit', True, (255, 255, 255))
    screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, 380))
    pygame.display.flip()

# Webcam
cap = cv2.VideoCapture(0)

def random_object():
    kind = random.choices(['banana', 'coconut', 'bomb'], weights=[0.7, 0.2, 0.1])[0]
    x = random.randint(50, WIDTH-50)
    y = -50
    return {'kind': kind, 'x': x, 'y': y, 'radius': 30, 'caught': False}

def draw_object(obj):
    color = BANANA_COLOR if obj['kind']=='banana' else COCONUT_COLOR if obj['kind']=='coconut' else BOMB_COLOR
    pygame.draw.circle(screen, color, (obj['x'], obj['y']), obj['radius'])

hand_traj = []
running = True

while running:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    monkey_tip = None
    hand_pointing = False
    hand_closed = False
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark
            h, w, _ = frame.shape
            tip_x, tip_y = int(lm[8].x * WIDTH), int(lm[8].y * HEIGHT)
            if is_index_finger_up(lm):
                monkey_tip = (tip_x, tip_y)
                hand_pointing = True
            if is_hand_closed(lm):
                hand_closed = True

    if game_state == 'menu':
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_difficulty = 'easy'
                elif event.key == pygame.K_2:
                    selected_difficulty = 'medium'
                elif event.key == pygame.K_3:
                    selected_difficulty = 'hard'
                elif event.key == pygame.K_s and selected_difficulty:
                    game_state = 'running'
                    score = 0
                    lives = 3
                    objects = []
                    frame_count = 0
                elif event.key == pygame.K_q:
                    running = False
        clock.tick(10)
        continue

    if game_state == 'running' and hand_closed:
        game_state = 'paused'
    elif game_state == 'paused' and hand_pointing and not hand_closed:
        game_state = 'running'

    if game_state == 'paused':
        draw_menu(paused=True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(10)
        continue

    screen.fill(BG_COLOR)
    if game_state == 'running':
        frame_count += 1
        if frame_count % spawn_rate == 0:
            objects.append(random_object())
        for obj in objects:
            obj['y'] += object_speed
        objects = [obj for obj in objects if obj['y'] < HEIGHT+50 and not obj['caught']]

    for obj in objects:
        draw_object(obj)

    if monkey_tip:
        pygame.draw.circle(screen, (255, 0, 0), monkey_tip, 15)
        for obj in objects:
            if not obj['caught']:
                dist = math.hypot(monkey_tip[0] - obj['x'], monkey_tip[1] - obj['y'])
                if dist < obj['radius'] + 15:
                    obj['caught'] = True
                    if obj['kind'] == 'banana':
                        score += 1
                    elif obj['kind'] == 'coconut':
                        if selected_difficulty == 'easy':
                            score = max(0, score - 1)
                        elif selected_difficulty == 'medium':
                            lives -= 1
                        else:  # hard
                            lives = 0
                    elif obj['kind'] == 'bomb':
                        if selected_difficulty == 'easy':
                            lives -= 1
                        else:
                            lives = 0

    if selected_difficulty == 'hard':
        for obj in objects:
            if obj['kind'] == 'banana' and obj['y'] >= HEIGHT and not obj['caught']:
                lives -= 1
                obj['caught'] = True

    score_text = font.render(f'Score: {score}', True, (255, 255, 255))
    lives_text = font.render(f'Lives: {lives}', True, (255, 0, 0))
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 50))

    if lives <= 0:
        game_state = 'menu'
        selected_difficulty = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)

cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
