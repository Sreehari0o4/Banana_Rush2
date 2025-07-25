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
    # Index tip (8) higher than pip (6) in y (for upright hand)
    return landmarks[8].y < landmarks[6].y and abs(landmarks[8].x - landmarks[6].x) < 0.1

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Banana Rush')
clock = pygame.time.Clock()

# Load assets (placeholder colors for now)
BANANA_COLOR = (255, 255, 0)
COCONUT_COLOR = (139, 69, 19)
BOMB_COLOR = (0, 0, 0)
BG_COLOR = (34, 139, 34)

font = pygame.font.SysFont('comicsans', 36)

# Game variables
score = 0
object_speed = 3
spawn_rate = 30  # frames
objects = []
frame_count = 0

# Game state
game_state = 'menu'  # 'menu', 'running', 'paused', 'quit'

def draw_menu(paused=False):
    screen.fill((20, 40, 20))
    title = font.render('Banana Rush', True, (255, 255, 0))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
    if not paused:
        start_text = font.render('S: Start Game', True, (255,255,255))
        screen.blit(start_text, (WIDTH//2 - start_text.get_width()//2, 220))
    else:
        point_text = font.render('Point to continue', True, (200,255,200))
        screen.blit(point_text, (WIDTH//2 - point_text.get_width()//2, 220))
    quit_text = font.render('Q: Quit', True, (255,255,255))
    screen.blit(quit_text, (WIDTH//2 - quit_text.get_width()//2, 270))
    pygame.display.flip()

# Webcam setup
cap = cv2.VideoCapture(0)


# Object class
def random_object():
    kind = random.choices(['banana', 'coconut', 'bomb'], weights=[0.7, 0.2, 0.1])[0]
    x = random.randint(50, WIDTH-50)
    y = -50
    return {'kind': kind, 'x': x, 'y': y, 'radius': 30, 'caught': False}

def draw_object(obj):
    color = BANANA_COLOR if obj['kind']=='banana' else COCONUT_COLOR if obj['kind']=='coconut' else BOMB_COLOR
    pygame.draw.circle(screen, color, (obj['x'], obj['y']), obj['radius'])

hand_traj = []

# Main game loop
running = True
while running:
    if game_state == 'menu':
        draw_menu(paused=False)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    game_state = 'running'
                elif event.key == pygame.K_q:
                    running = False
        clock.tick(10)
        continue
    elif game_state == 'paused':
        draw_menu(paused=True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
        clock.tick(10)
        continue

    screen.fill(BG_COLOR)
    # Webcam frame
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    monkey_tip = None
    hand_pointing = False
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            lm = hand_landmarks.landmark
            h, w, _ = frame.shape
            tip_x, tip_y = int(lm[8].x * WIDTH), int(lm[8].y * HEIGHT)
            if is_index_finger_up(lm):
                monkey_tip = (tip_x, tip_y)
                hand_pointing = True
    # Pause logic: only update game state if hand is pointing
    if hand_pointing:
        frame_count += 1
        # Spawn objects
        if frame_count % spawn_rate == 0:
            objects.append(random_object())
        # Move objects
        for obj in objects:
            obj['y'] += object_speed
        # Remove off-screen objects
        objects = [obj for obj in objects if obj['y'] < HEIGHT+50 and not obj['caught']]
    else:
        if game_state == 'running':
            game_state = 'paused'
    # Draw objects (always)
    for obj in objects:
        draw_object(obj)
    # Draw monkey hand (red dot) and allow catching only if pointing
    if monkey_tip:
        pygame.draw.circle(screen, (255, 0, 0), monkey_tip, 15)
        # Check for catching objects
        for obj in objects:
            if not obj['caught']:
                dist = math.hypot(monkey_tip[0] - obj['x'], monkey_tip[1] - obj['y'])
                if dist < obj['radius'] + 15:
                    obj['caught'] = True
                    if obj['kind'] == 'banana':
                        score += 1
                    elif obj['kind'] == 'bomb':
                        score = max(0, score-5)
                    elif obj['kind'] == 'coconut':
                        score = max(0, score-2)
    # Increase difficulty
    if score and score % 10 == 0:
        object_speed = 3 + score//10
        spawn_rate = max(10, 30 - score//5)
    # Draw score
    score_text = font.render(f'Score: {score}', True, (255,255,255))
    screen.blit(score_text, (10, 10))
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pygame.display.flip()
    clock.tick(30)

cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()
