import pygame
import sys
pygame.init()
font = pygame.font.SysFont("consolas",22)
small_font = pygame.font.SysFont("consolas",18)
def draw_hud():
    panel = pygame.Rect(780,0,220,HEIGHT)
    pygame.draw.rect(screen,(35,35,35),panel)
    pygame.draw.line(
        screen,
        (70,70,70),
        (780,0),
        (780,HEIGHT),
        2
    )
    title=font.render("ASTERIA", True, (255,255,255))
    screen.blit(title,(820,20))
    battery=85
    battery_text= small_font.render(
        "Battery",
        True,
        (255,255,255)
        )
    screen.blit(battery_text,(800,70))
    pygame.draw.rect(screen,(80,80,80),(800,100,150,20))
    pygame.draw.rect(
        screen,
        (0,220,0),
        (800,100,int(150*battery/100),20)
    )
    mission = "Explore"
    mission_text=small_font.render(
        f"Mission: {mission}",
        True,
        (255,255,255)
    )
    screen.blit(mission_text,(800,150))
    decision= "Move Forward"
    decision_text= small_font.render(
        f"Decision:{decision}",
        True,
        (255,255,255)
    )
    screen.blit(decision_text,(800,220))
    temperature= 26
    temp_text = small_font.render(
        f"Temperature:{temperature}C",
        True,
        (255,255,255)
    )
    screen.blit(temp_text,(800,280))
    status = "SAFE"
    status_text = small_font.render(
        f"Status: {status}",
        True,
        (0,255,0)
    )
    screen.blit(status_text,(800,330))
    
WIDTH = 1000
HEIGHT = 700
screen= pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("ASTERIA 1.0 - Autonomous Explorer")
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running = False
    screen.fill((20,20,20))
    GRID_SIZE = 40

    for x in range(0, 780, GRID_SIZE):
        pygame.draw.line(
            screen,
            (40, 40, 40),
            (x, 0),
            (x, HEIGHT)
        )

    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(
            screen,
            (40, 40, 40),
            (0, y),
            (WIDTH, y)
        )
    robot_x = 500
    robot_y= 350

    pygame.draw.circle(
        screen,
        (0,120,255),
        (robot_x,robot_y),
        28
    )
    # ---------- Robot Body ----------

    body = pygame.Rect(robot_x-18, robot_y-15, 36, 30)
    pygame.draw.rect(screen, (0,170,255), body, border_radius=8)

# Left wheel
    pygame.draw.rect(
        screen,
        (30,30,30),
        (robot_x-24, robot_y-14, 6, 28),
        border_radius=2
    )

# Right wheel
    pygame.draw.rect(
        screen,
        (30,30,30),
        (robot_x+18, robot_y-14, 6, 28),
        border_radius=2
    )

# Camera
    pygame.draw.circle(
        screen,
        (255,255,255),
        (robot_x,robot_y-8),
        4
    )

# LED
    pygame.draw.circle(
        screen,
        (0,255,255),
        (robot_x,robot_y+8),
        3
    )

# Heading Arrow
    pygame.draw.line(
        screen,
        (255,255,255),
        (robot_x,robot_y),
        (robot_x,robot_y-28),
        3
    )
    sensor_length = 120

    pygame.draw.line(
        screen,
        (0,255,255),
        (robot_x,robot_y),
        (robot_x,robot_y-sensor_length),
        2
    )
    pygame.draw.line(
        screen,
        (255,255,0),
        (robot_x,robot_y),
        (robot_x-sensor_length,robot_y),
        2
    )
    pygame.draw.line(
        screen,
        (255,255,0),
        (robot_x,robot_y),
        (robot_x+sensor_length,robot_y),
        2
    )
    pygame.draw.line(
        screen,
        (255,150,0),
        (robot_x,robot_y),
        (robot_x,robot_y+sensor_length),
        2
    )
    draw_hud()
    pygame.display.update()
    clock.tick(60)
pygame.quit()
sys.exit()
