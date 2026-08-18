import pygame
import random
import math
import sys
from asteria_core import AsteriaConfig, Environment, EnvironmentAnalyzer

# Display Viewport Parameters
WIDTH, HEIGHT = 1150, 700
WORLD_WIDTH, WORLD_HEIGHT = 2000, 2000
FPS = 60
TILE_SIZE = 45

WHITE = (245, 245, 250)
BLACK = (10, 12, 18)
RED = (255, 70, 70)
BLUE = (0, 160, 255)
GREEN = (0, 255, 140)
GRAY = (55, 62, 75)
PANEL_BG = (16, 20, 30)

class WorldObstacle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        if -self.radius < sx < WIDTH - 250 and -self.radius < sy < HEIGHT:
            pygame.draw.circle(screen, (40, 45, 55), (int(sx), int(sy)), self.radius)
            pygame.draw.circle(screen, (230, 90, 60), (int(sx), int(sy)), self.radius, 2)

class SimulationRover:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0  # Float tracking continuous rotation orientation heading
        self.sensor_range = 150
        self.trail_history = []
        self.active_beams = [150] * 4

    def cast_lidar_rays(self, obstacles, max_w, max_h):
        # Ray directions relative to rotation: Front (0), Left (-90), Right (+90), Rear (180)
        offsets = [0, -90, 90, 180]
        distances = [self.sensor_range] * 4
        
        for i, offset in enumerate(offsets):
            rad = math.radians(self.angle + offset)
            for step in range(5, self.sensor_range, 3):
                tx = self.x + step * math.cos(rad)
                ty = self.y + step * math.sin(rad)
                
                # Check absolute boundaries mapping
                if tx < 40 or tx > max_w - 40 or ty < 40 or ty > max_h - 40:
                    distances[i] = step
                    break
                # Check solid circular obstacles collision intersections
                hit = False
                for obs in obstacles:
                    if math.hypot(tx - obs.x, ty - obs.y) <= obs.radius:
                        distances[i] = step
                        hit = True
                        break
                if hit: break
        self.active_beams = distances
        return distances

    def execute_kinematics(self, core_direction):
        # Translates your original discrete software commands directly into smooth vector kinematics
        if core_direction == "Forward":
            rad = math.radians(self.angle)
            self.x += 2.2 * math.cos(rad)
            self.y += 2.2 * math.sin(rad)
        elif core_direction == "Left":
            self.angle = (self.angle - 4) % 360
        elif core_direction == "Right":
            self.angle = (self.angle + 4) % 360
        elif core_direction == "Rear":
            rad = math.radians(self.angle)
            self.x -= 1.4 * math.cos(rad)
            self.y -= 1.4 * math.sin(rad)

        # Log trailing coordinates path mesh
        if not self.trail_history or math.hypot(self.x - self.trail_history[-1][0], self.y - self.trail_history[-1][1]) > 8:
            self.trail_history.append((self.x, self.y))
            if len(self.trail_history) > 60: self.trail_history.pop(0)

    def draw(self, screen, camera_x, camera_y):
        sx, sy = self.x - camera_x, self.y - camera_y

        # Draw Sensor Laser Beam Cones Indicators
        offsets = [0, -90, 90, 180]
        for i, offset in enumerate(offsets):
            rad_beam = math.radians(self.angle + offset)
            dist = self.active_beams[i]
            tx = sx + dist * math.cos(rad_beam)
            ty = sy + dist * math.sin(rad_beam)
            beam_color = RED if dist < 25 else (0, 170, 255)
            pygame.draw.line(screen, beam_color, (sx, sy), (tx, ty), 1)
            pygame.draw.circle(screen, beam_color, (int(tx), int(ty)), 3)

        # Draw Fading Trail history path mapping lines
        for idx, pt in enumerate(self.trail_history):
            px, py = pt[0] - camera_x, pt[1] - camera_y
            if 0 < px < WIDTH - 250 and 0 < py < HEIGHT:
                alpha = int((idx / len(self.trail_history)) * 255)
                trail_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
                trail_surface.fill((0, 255, 140, alpha))
                screen.blit(trail_surface, (px - 2, py - 2))

        # Render Top-Down 6-Wheeled Rover Chassis Model Blueprint
        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        cos_p, sin_p = math.cos(rad + math.pi/2), math.sin(rad + math.pi/2)

        # Draw 6 independent suspension wheel rigs
        wheel_offsets = [(12, 12), (0, 12), (-12, 12), (12, -12), (0, -12), (-12, -12)]
        for wx, wy in wheel_offsets:
            cx = sx + (wx * cos_a + wy * cos_p)
            cy = sy + (wx * sin_a + wy * sin_p)
            wheel_surf = pygame.Surface((10, 5), pygame.SRCALPHA)
            wheel_surf.fill((35, 35, 40))
            rot_wheel = pygame.transform.rotate(wheel_surf, -self.angle)
            screen.blit(rot_wheel, rot_wheel.get_rect(center=(int(cx), int(cy))).topleft)

        # Draw main triangular tool carriage structure chassis frame
        points = [
            (sx + 16 * cos_a, sy + 16 * sin_a),
            (sx - 12 * cos_a + 10 * cos_p, sy - 12 * sin_a + 10 * sin_p),
            (sx - 12 * cos_a - 10 * cos_p, sy - 12 * sin_a - 10 * sin_p)
        ]
        pygame.draw.polygon(screen, (225, 230, 240), points)
        pygame.draw.polygon(screen, (150, 160, 175), points, 2)

        # Render Core Blue Solar Panel Array Grid Mesh Matrix
        pygame.draw.circle(screen, (25, 60, 130), (int(sx - 3 * cos_a), int(sy - 3 * sin_a)), 6)
        pygame.draw.circle(screen, (50, 120, 245), (int(sx - 3 * cos_a), int(sy - 3 * sin_a)), 6, 1)

class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("Courier", 14, bold=True)

    def draw(self, screen, config, analyzer):
        panel_x = WIDTH - 250
        pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, 250, HEIGHT))
        pygame.draw.line(screen, GREEN, (panel_x, 0), (panel_x, HEIGHT), 2)

        hud_elements = [
            ("== ORIGINAL CONFIG REG ==", (0, 180, 255)),
            (f"Robot Name : {config.robot_name}", WHITE),
            (f"Wheel Rad  : {config.wheel_radius} cm", WHITE),
            (f"Wheel Base : {config.wheel_base} cm", WHITE),
            ("-" * 22, GRAY),
            ("== CORE DRIVE TELEMETRY ==", (0, 180, 255)),
            (f"Active Cmd : {config.direction}", (255, 215, 0) if config.direction != "Forward" else GREEN),
            (f"Max Speed  : {config.max_speed} cm/s", WHITE),
            (f"Is Moving  : {config.is_moving}", GREEN if config.is_moving else RED),
            (f"Braking St : {config.braking}", RED if config.braking else WHITE),
            (f"Battery Cell: {config.battery}%", GREEN if config.battery > 25 else RED),
            ("-" * 22, GRAY),
            ("== PAYLOAD SCANNERS ==", (0, 180, 255)),
            (f"Classification: {analyzer.analyze_temperature()}", GREEN),
            (f"Core Thermal : {analyzer.environment.temperature} K", WHITE),
            (" (Hold Up/Down Key)", (140, 155, 170)),
            ("-" * 22, GRAY),
            ("== LOGGED DISTANCE REG ==", (0, 180, 255)),
            (f"Front Lidar : {int(config.distance) if config.distance else 0} cm", WHITE),
            (f"Left Lidar  : {int(config.distance_left) if config.distance_left else 0} cm", WHITE),
            (f"Right Lidar : {int(config.distance_right) if config.distance_right else 0} cm", WHITE),
            (f"Rear Lidar  : {int(config.distance_rear) if config.distance_rear else 0} cm", WHITE),
        ]

        for idx, (text, color) in enumerate(hud_elements):
            screen.blit(self.font.render(text, True, color), (panel_x + 12, 25 + (idx * 23)))

class SimulationEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Asteria Structural Verification Core Simulator")
        self.clock = pygame.time.Clock()
        self.hud = HUD()

        # Generate continuous scrolling coordinates background map setup
        self.obstacles = []
        for _ in range(50):
            self.obstacles.append(WorldObstacle(random.randint(100, WORLD_WIDTH-100), random.randint(100, WORLD_HEIGHT-100), random.randint(20, 45)))

        self.sim_robot = SimulationRover(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.camera_x, self.camera_y = 0, 0

        # INSTANTIATE YOUR ORIGINAL SOFTWARE CORE LAYER BLUEPRINTS
        self.config = AsteriaConfig("Asteria-02", 20)
        self.environment = Environment()
        self.analyzer = EnvironmentAnalyzer(self.environment)

    def update_viewport_camera(self):
        self.camera_x = max(0, min(self.sim_robot.x - (WIDTH - 250) // 2, WORLD_WIDTH - (WIDTH - 250)))
        self.camera_y = max(0, min(self.sim_robot.y - HEIGHT // 2, WORLD_HEIGHT - HEIGHT))

    def run_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

            # Environmental manual override check hooks (Hold UP/DOWN arrow keys)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]: self.environment.temperature += 1
            if keys[pygame.K_DOWN]: self.environment.temperature -= 1

            # 1. Update true spatial sensor tracking distance floats data tables
            beams = self.sim_robot.cast_lidar_rays(self.obstacles, WORLD_WIDTH, WORLD_HEIGHT)

            # 2. Update your original software properties with the sensor floats
            self.config.update_distance(beams[0])       # Front
            self.config.update_distance_left(beams[1])  # Left
            self.config.update_distance_right(beams[2]) # Right
            self.config.update_distance_rear(beams[3])  # Rear
# Also mirror data back into your original environment instance block propertiesself.environment.update_front_distance(beams[0])self.environment.update_left_distance(beams[1])self.environment.update_right_distance(beams[2])self.environment.update_rear_distance(beams[3])# 3. RUN YOUR UNTOUCHED AUTONOMOUS PROCESSING METHODSself.config.avoid_obstacles()self.config.brakes()self.config.remember_distance()# 4. Extract your precise command outputs and map them to fluid engine tracking motionself.sim_robot.execute_kinematics(self.config.direction)self.update_viewport_camera()# 5. Paint current canvas view frames layersself.screen.fill(BLACK)# Draw ground grid lines mesh matrix layer boundsstart_x = int(self.camera_x % TILE_SIZE)start_y = int(self.camera_y % TILE_SIZE)for x in range(-start_x, WIDTH - 250, TILE_SIZE):pygame.draw.line(self.screen, (22, 26, 35), (x, 0), (x, HEIGHT), 1)for y in range(-start_y, HEIGHT, TILE_SIZE):pygame.draw.line(self.screen, (22, 26, 35), (0, y), (WIDTH - 250, y), 1)# Draw structural map obstacles, robot tracks, and text dashboard registriesfor obs in self.obstacles: obs.draw(self.screen, self.camera_x, self.camera_y)self.sim_robot.draw(self.screen, self.camera_x, self.camera_y)self.hud.draw(self.screen, self.config, self.analyzer)pygame.display.update()self.clock.tick(FPS)pygame.quit()if name == "main":SimulationEngine().run_loop()
            # Also mirror data back into your original environment instance block properties
            self.environment.update_front_distance(beams[0])
            self.environment.update_left_distance(beams[1])
            self.environment.update_right_distance(beams[2])
            self.environment.update_rear_distance(beams[3])

            # 3. RUN YOUR UNTOUCHED AUTONOMOUS PROCESSING METHODS
            self.config.avoid_obstacles()
            self.config.brakes()
            self.config.remember_distance()

            # 4. Extract your precise command outputs and map them to fluid engine tracking motion
            self.sim_robot.execute_kinematics(self.config.direction)
            self.update_viewport_camera()

            # 5. Paint current canvas view frames layers
            self.screen.fill(BLACK)
            
            # Draw ground grid lines mesh matrix layer bounds
            start_x = int(self.camera_x % TILE_SIZE)
            start_y = int(self.camera_y % TILE_SIZE)
            for x in range(-start_x, WIDTH - 250, TILE_SIZE):
                pygame.draw.line(self.screen, (22, 26, 35), (x, 0), (x, HEIGHT), 1)
            for y in range(-start_y, HEIGHT, TILE_SIZE):
                pygame.draw.line(self.screen, (22, 26, 35), (0, y), (WIDTH - 250, y), 1)

            # Draw structural map obstacles, robot tracks, and text dashboard registries
            for obs in self.obstacles: 
                obs.draw(self.screen, self.camera_x, self.camera_y)
                
            self.sim_robot.draw(self.screen, self.camera_x, self.camera_y)
            self.hud.draw(self.screen, self.config, self.analyzer)

            pygame.display.update()
            self.clock.tick(FPS)
            
        pygame.quit()

if __name__ == "__main__":
    SimulationEngine().run_loop()
