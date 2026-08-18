import pygame
import random
import math
import sys

# ==========================================
# 1. PROJECT SPECIFIC CONSTANTS
# ==========================================
WIDTH, HEIGHT = 1150, 700
FPS = 60

# Structural High-Contrast Palette Vectors
WHITE = (235, 240, 250)
BLACK = (8, 10, 16)
RED = (255, 65, 65)
BLUE = (30, 100, 220)
GREEN = (0, 255, 140)
GRAY = (55, 65, 80)
PANEL_BG = (12, 16, 26)

# Terrain Enumerations
GRASS = 0
SAND = 1
WATER = 2
ROCK = 3

# ==========================================
# 2. CORE SYSTEM EXPERT SCHEMES (asteria_core.py)
# ==========================================
class AsteriaConfig:
    def __init__(self, robot_name, max_speed):
        self.robot_name = robot_name
        self.max_speed = max_speed
        self.battery = 100.0
        self.direction = "Forward"
        self.distance = 250
        self.distance_left = 250
        self.distance_right = 250
        self.distance_rear = 250

    def update_distance(self, f): self.distance = f
    def update_distance_left(self, l): self.distance_left = l
    def update_distance_right(self, r): self.distance_right = r
    def update_distance_rear(self, b): self.distance_rear = b

    def consume_power(self, amount):
        self.battery = max(0.0, self.battery - amount)
        if self.battery <= 0: self.direction = "Stopped"

class Environment:
    def __init__(self):
        self.temperature = 220  # Kelvin (Initial Mars-like status)
        self.front_distance = 250
        self.rear_distance = 250
        self.left_distance = 250
        self.right_distance = 250

    def update_front_distance(self, d): self.front_distance = d
    def update_rear_distance(self, d): self.rear_distance = d
    def update_left_distance(self, d): self.left_distance = d
    def update_right_distance(self, d): self.right_distance = d

class EnvironmentAnalyzer:
    def __init__(self, environment):
        self.environment = environment

    def analyze_temperature(self):
        t = self.environment.temperature
        if t < 30: return "Deep Space Void"
        if t < 150: return "Comet Ice Bed"
        if t < 273: return "Martian Regolith"
        if t < 310: return "Terrestrial Zone"
        return "Venusian Flare Plain"

    def overall_status(self):
        warnings = []
        if self.environment.temperature < 80: warnings.append("THERMAL STRESS: CRYOGENIC COLD")
        if self.environment.temperature > 320: warnings.append("THERMAL STRESS: INTENSE HEAT")
        if self.environment.front_distance < 60: warnings.append("COLLISION RISK: OBSTACLE REAR")
        return {"Status": "DANGER" if warnings else "SAFE", "Warnings": warnings}

class MissionController:
    def choose_mission(self, battery, status):
        if battery < 20: return "Recharge Protocol"
        if status == "DANGER": return "Evasive Navigation"
        return "Autonomous Grid Survey"

class AsteriaBrain:
    def __init__(self, analyzer, robot, controller, memory):
        self.environment_analyzer = analyzer
        self.robot = robot
        self.mission_controller = controller

    def run_cycle(self):
        status_report = self.environment_analyzer.overall_status()
        mission = self.mission_controller.choose_mission(self.robot.battery, status_report["Status"])
        
        if mission == "Recharge Protocol":
            self.robot.direction = "Stopped"
            decision = "STANDBY: DEPLOYING SOLAR CHARGERS"
        elif mission == "Evasive Navigation":
            if self.robot.distance_left >= self.robot.distance_right and self.robot.distance_left > 45:
                self.robot.direction = "Left"
                decision = "EVASION: SHIFTING PORT TRACK GEARS"
            elif self.robot.distance_right > 45:
                self.robot.direction = "Right"
                decision = "EVASION: SHIFTING STARBOARD GEARS"
            else:
                self.robot.direction = "Rear"
                decision = "ENTRAPPED: ENGAGING INVERSE MATRIX"
        else:
            self.robot.direction = "Forward"
            decision = "SURVEY: LOGGING PROCEDURAL GRID DATA"

        self.robot.consume_power(0.025 if self.robot.direction != "Stopped" else -0.15)
        return {"Mission": mission, "Status": status_report["Status"], "Decision": decision, "Warnings": status_report["Warnings"]}

class AsteriaInterface:
    def __init__(self, brain):
        self.brain = brain

    def update_sensors(self, sensor_data):
        env = self.brain.environment_analyzer.environment
        env.update_front_distance(sensor_data.get("front", 250))
        env.update_rear_distance(sensor_data.get("rear", 250))
        env.update_left_distance(sensor_data.get("left", 250))
        env.update_right_distance(sensor_data.get("right", 250))

# ==========================================
# 3. ADVANCED WORLD INTERFACE SECTOR (world.py)
# ==========================================
class Tile:
    def __init__(self, tile_type, size):
        self.tile_type = tile_type
        self.size = size
        # Build strict dynamic color assignment variables
        if tile_type == GRASS: self.color = (38, 55, 42)
        elif tile_type == SAND: self.color = (130, 112, 85)
        elif tile_type == WATER: self.color = (25, 45, 82)
        elif tile_type == ROCK: self.color = (48, 52, 60)
        else: self.color = BLACK

        # Pre-seed deterministic detail micro-coordinates to completely prevent randomized canvas flickering
        random.seed(random.randint(0, 100000))
        self.details = [(random.randint(3, size - 3), random.randint(3, size - 3)) for _ in range(3)]

    def draw(self, screen, x, y, camera_x, camera_y):
        rect = pygame.Rect(x * self.size - camera_x, y * self.size - camera_y, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (self.color[0]+4, self.color[1]+4, self.color[2]+4), rect, 1)

        # Draw micro-texture layers with exact coordinate clamping markers
        if self.tile_type == GRASS:
            for dx, dy in self.details:
                pygame.draw.circle(screen, (22, 36, 26), (rect.x + dx, rect.y + dy), 2)
        elif self.tile_type == SAND:
            for dx, dy in self.details:
                pygame.draw.circle(screen, (170, 150, 120), (rect.x + dx, rect.y + dy), 1)
        elif self.tile_type == ROCK:
            pygame.draw.line(screen, (34, 38, 44), (rect.x + 4, rect.y + 4), (rect.x + self.size - 4, rect.y + self.size - 4), 2)
        elif self.tile_type == WATER:
            pygame.draw.line(screen, (40, 80, 140), (rect.x + 4, rect.y + self.size // 2), (rect.x + self.size - 4, rect.y + self.size // 2), 2)

class World:
    def __init__(self, width=120, height=120, tile_size=40):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.tiles = []
        self.obstacles = []  # Explicit dynamic collision entities mapping array
        self.generate_world()
        self.generate_obstacles()

    def generate_world(self):
        random.seed()  # Let runtime environments establish seed parameters naturally
        for y in range(self.height):
            row = []
            for x in range(self.width):
                chance = random.random()
                if chance < 0.62: terrain = GRASS
                elif chance < 0.78: terrain = SAND
                elif chance < 0.91: terrain = ROCK
                else: terrain = WATER
                row.append(Tile(terrain, self.tile_size))
            self.tiles.append(row)

    def generate_obstacles(self):
        for _ in range(90):
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            obstacle = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
            self.obstacles.append(obstacle)
        # Dedicated corner safety calibration coordinate check injection
        self.obstacles.append(pygame.Rect(800, 650, self.tile_size, self.tile_size))

    def get_tile(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height: return None
        return self.tiles[y][x]

    def draw(self, screen, camera_x, camera_y):
        # PERFORMANCE FIX: Frustum Viewport Slicing optimization (Only draw visible elements)
        start_x = max(0, int(camera_x // self.tile_size))
        end_x = min(self.width, int((camera_x + WIDTH - 250) // self.tile_size) + 1)
        start_y = max(0, int(camera_y // self.tile_size))
        end_y = min(self.height, int((camera_y + HEIGHT) // self.tile_size) + 1)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                self.tiles[y][x].draw(screen, x, y, camera_x, camera_y)

        # Draw obstacles
        for obstacle in self.obstacles:
            obs_rect = pygame.Rect(obstacle.x - camera_x, obstacle.y - camera_y, obstacle.width, obstacle.height)
            if -self.tile_size < obs_rect.x < WIDTH - 250 and -self.tile_size < obs_rect.y < HEIGHT:
                pygame.draw.rect(screen, (160, 50, 50), obs_rect)
                pygame.draw.rect(screen, RED, obs_rect, 2)

# ==========================================
# 4. PHYSICAL ROVER MECHANICS DESIGN (robot.py)
# ==========================================
class Robot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0  
        self.speed = 0.0
        self.sensor_range = 250
        self.history = []

    def update_sensors(self, obstacles, max_world_w, max_world_h):
        angles = [0, -45, 45, 180]
        distances = [self.sensor_range] * 4

        for i, offset in enumerate(angles):
            rad = math.radians(self.angle + offset)
            for step in range(5, self.sensor_range, 4):
                tx = self.x + step * math.cos(rad)
                ty = self.y + step * math.sin(rad)
                if tx < 0 or tx > max_world_w or ty < 0 or ty > max_world_h:
                    distances[i] = step
                    break
 # Solid obstacle intersect box collision validation loopcollided = Falsefor obs in obstacles:if obs.collidepoint(tx, ty):distances(i) = stepcollided = Truebreakif collided: breakreturn {"front": distances(0), "left": distances(1), "right": distances(2), "rear": distances(3)}def autonomous_move(self, command, max_world_w, max_world_h):if command == "Forward": self.speed = 3.0elif command == "Left":self.angle = (self.angle - 5) % 360self.speed = 1.0elif command == "Right":self.angle = (self.angle + 5) % 360self.speed = 1.0elif command == "Rear": self.speed = -1.5else: self.speed = 0.0rad = math.radians(self.angle)self.x += self.speed * math.cos(rad)self.y += self.speed * math.sin(rad)# Clamp coordinates tightly inside map marginsself.x = max(50, min(self.x, max_world_w - 50))self.y = max(50, min(self.y, max_world_h - 50))if not self.history or math.hypot(self.x - self.history(-1), self.y - self.history(-1)) > 8:self.history.append((self.x, self.y))if len(self.history) > 80: self.history.pop(0)def draw(self, screen, camera_x, camera_y):screen_x = self.x - camera_xscreen_y = self.y - camera_y# Draw trajectory breadcrumbs trail path line mappingsfor idx, pt in enumerate(self.history):px, py = pt - camera_x, pt - camera_yif 0 < px < WIDTH - 250 and 0 < py < HEIGHT:alpha = int((idx / len(self.history)) * 255)trail_surface = pygame.Surface((4, 4), pygame.SRCALPHA)trail_surface.fill((0, 255, 140, alpha))screen.blit(trail_surface, (px - 2, py - 2))# Dynamic rotational coordinate polygon draw configurationsrad = math.radians(self.angle)pt_front = (screen_x + 18 * math.cos(rad), screen_y + 18 * math.sin(rad))pt_back1 = (screen_x + 11 * math.cos(rad + 2.4), screen_y + 11 * math.sin(rad + 2.4))pt_back2 = (screen_x + 11 * math.cos(rad - 2.4), screen_y + 11 * math.sin(rad - 2.4))pygame.draw.polygon(screen, GREEN, (pt_front, pt_back1, pt_back2))pygame.draw.circle(screen, WHITE, (int(screen_x), int(screen_y)), 3)
                # Canvas perimeter validation check constraints
class UI:
    def init(self):
        self.font = pygame.font.SysFont("Courier", 14, bold=True)
        
    def draw(self, screen, robot, brain, zone, result):
        panel_x = WIDTH - 250 
        pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, 250, HEIGHT))
        pygame.draw.line(screen, GREEN, (panel_x, 0), (panel_x, HEIGHT), 2)
        status_colors = {"SAFE": GREEN, "DANGER": RED}
        stat_color = status_colors.get(result("Status"), WHITE)
        hud_elements = [("== DECISION CONTROLS == ", (0, 180, 255)),(f"Task Mode: {result('Mission')}", WHITE),(f"Risk Rank: {result('Status')}", stat_color),("-" * 22, GRAY),("== CLIMATE MONITORING == ", (0, 180, 255)),(f"Zone : {zone}", GREEN),(f"Temp : {brain.environment_analyzer.environment.temperature} K", WHITE),(" (Hold Up/Down Key)", (160, 175, 190)),("-" * 22, GRAY),("== ELECTRICAL MATRIX == ", (0, 180, 255)),(f"Battery  : {brain.robot.battery:.1f}%", GREEN if brain.robot.battery > 25 else RED),(f"Motion   : {brain.robot.direction}", WHITE),(f"Angle    : {int(robot.angle)} deg", WHITE),("-" * 22, GRAY),("== TELEMETRY ARRAYS ==  ", (0, 180, 255)),(f"LIDAR F  : {int(brain.robot.distance)} cm", WHITE),(f"LIDAR L  : {int(brain.robot.distance_left)} cm", WHITE),(f"LIDAR R  : {int(brain.robot.distance_right)} cm", WHITE),(f"LIDAR B  : {int(brain.robot.distance_rear)} cm", WHITE),]
        for idx, (text, color) in enumerate(hud_elements):screen.blit(self.font.render(text, True, color), (panel_x + 15, 25 + (idx * 24)))# Draw alerts panel tracking logs block matrix containerpygame.draw.rect(screen, (20, 26, 40), (panel_x + 10, 510, 230, 160))screen.blit(self.font.render("CRITICAL HARDWARE ALERTS:", True, (150, 165, 185)), (panel_x + 18, 520))if result("Warnings"):for i, warn in enumerate(result("Warnings")(:4)):screen.blit(self.font.render(f"! {warn}", True, RED), (panel_x + 18, 545 + (i * 20)))else:screen.blit(self.font.render("SYSTEM NOMINAL: NO FAULTS", True, GREEN), (panel_x + 18, 555))