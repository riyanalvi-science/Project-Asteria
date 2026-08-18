import pygame
import random
import math
import sys

# --- ROVER CONFIGURATION & CONTROL ENGINE ---
class AsteriaConfig:
    def __init__(self, name, x, y):
        self.robot_name = name
        self.x = x
        self.y = y
        self.angle = 0  
        self.speed = 0
        self.battery = 100.0
        self.direction = "Standby"
        
        # Sensor Registers
        self.distance = 250
        self.distance_left = 250
        self.distance_right = 250
        self.distance_rear = 250
        self.distance_history = []  # Path memory tracking

    def can_move_forward(self): return self.distance > 40
    def can_turn_left(self): return self.distance_left > 40
    def can_turn_right(self): return self.distance_right > 40
    def can_reverse(self): return self.distance_rear > 40

    def move_forward(self):
        self.direction = "Forward"
        self.speed = 2.5

    def turn_left(self):
        self.direction = "Left"
        self.angle = (self.angle - 8) % 360
        self.speed = 0.8

    def turn_right(self):
        self.direction = "Right"
        self.angle = (self.angle + 8) % 360
        self.speed = 0.8

    def reverse(self):
        self.direction = "Rear"
        self.speed = -1.5

    def stop_robot(self):
        self.direction = "Stopped"
        self.speed = 0

    def update_position(self):
        rad = math.radians(self.angle)
        self.x += self.speed * math.cos(rad)
        self.y += self.speed * math.sin(rad)
        
        # Keep within boundaries
        self.x = max(40, min(self.x, 760))
        self.y = max(40, min(self.y, 560))
        
        # Log location memory breadcrumbs
        if len(self.distance_history) == 0 or math.hypot(self.x - self.distance_history[-1][0], self.y - self.distance_history[-1][1]) > 8:
            self.distance_history.append((self.x, self.y))
            if len(self.distance_history) > 60:  # Bound memory leak
                self.distance_history.pop(0)

        # Active mission battery depletion
        if self.speed != 0:
            self.battery = max(0.0, self.battery - 0.04)


# --- PHYSICAL LEVEL & ENVIRONMENT ATOM ---
class Environment:
    def __init__(self):
        self.temperature = 220  # Kelvin (Initial Mars-like)
        self.humidity = 2        # Interplanetary space/desert
        self.luminosity = 90     # Twilight
        self.obstacles = [(random.randint(120, 700), random.randint(100, 500), random.randint(20, 45)) for _ in range(10)]

    def cast_sensor_ray(self, start_x, start_y, angle_offset, rover_angle):
        rad = math.radians(rover_angle + angle_offset)
        for d in range(1, 250, 3):
            tx = start_x + d * math.cos(rad)
            ty = start_y + d * math.sin(rad)
            if tx < 0 or tx > 800 or ty < 0 or ty > 600:
                return d
            for obs_x, obs_y, radius in self.obstacles:
                if math.hypot(tx - obs_x, ty - obs_y) <= radius:
                    return d
        return 250


# --- INTELLIGENT EXPERT SYSTEMS ANALYZER ---
class EnvironmentAnalyzer:
    def __init__(self, environment):
        self.environment = environment

    def analyze_temperature(self):
        t = self.environment.temperature
        if t < 30: return "Deep space like"
        elif t < 150: return "Comet like"
        elif t < 273: return "Mars like"
        elif t < 310: return "Earth like"
        elif t < 330: return "Warm Earth like"
        elif t < 800: return "Venus like"
        else: return "Mercury Day-side like"

    def overall_status(self, f_dist, l_dist, r_dist):
        warnings = []
        if self.environment.temperature > 320: warnings.append("THERMAL STRESS: HIGH HEAT")
        elif self.environment.temperature < 100: warnings.append("THERMAL STRESS: DEEP COLD")
        
        if f_dist < 40: warnings.append("OBSTACLE AHEAD")
        if l_dist < 25: warnings.append("FLANK WALL LEFT")
        if r_dist < 25: warnings.append("FLANK WALL RIGHT")
        
        if len(warnings) == 0: return {"Status": "SAFE", "Warnings": []}
        elif len(warnings) <= 2: return {"Status": "RISKY", "Warnings": warnings}
        return {"Status": "DANGER", "Warnings": warnings}


class MissionController:
    def choose_mission(self, battery, status):
        if battery < 20: return "Recharge"
        if status == "DANGER": return "Avoid Danger"
        if status == "RISKY": return "Proceed Carefully"
        return "Explore"


class AsteriaBrain:
    def __init__(self, robot, env):
        self.robot = robot
        self.env = env
        self.analyzer = EnvironmentAnalyzer(env)
        self.mc = MissionController()

    def run_cycle(self):
        # 1. Update distance parameters from lidar array rays
        self.robot.distance = self.env.cast_sensor_ray(self.robot.x, self.robot.y, 0, self.robot.angle)
        self.robot.distance_left = self.env.cast_sensor_ray(self.robot.x, self.robot.y, -45, self.robot.angle)
        self.robot.distance_right = self.env.cast_sensor_ray(self.robot.x, self.robot.y, 45, self.robot.angle)
        self.robot.distance_rear = self.env.cast_sensor_ray(self.robot.x, self.robot.y, 180, self.robot.angle)

        # 2. Check sensory risk bounds via core framework analyzer
        status_report = self.analyzer.overall_status(self.robot.distance, self.robot.distance_left, self.robot.distance_right)
        
        # 3. Determine high-level mission profile
        mission = self.mc.choose_mission(self.robot.battery, status_report["Status"])

        # 4. Process Navigation Decision Tree Map logic
        if mission == "Recharge":
            self.robot.stop_robot()
            decision = "EMERGENCY: SYSTEM STANDBY FOR POWER SEED"
        elif mission == "Avoid Danger" or mission == "Proceed Carefully":
            if self.robot.can_turn_left() and self.robot.distance_left >= self.robot.distance_right:
                self.robot.turn_left()
                decision = "ROUTE: ALTERING BEARING LEFT"
            elif self.robot.can_turn_right():
                self.robot.turn_right()
                decision = "ROUTE: ALTERING BEARING RIGHT"
            elif self.robot.can_reverse():
                self.robot.reverse()
                decision = "PATH LOCKED: ENGAGING REVERSAL COMPONENT"
            else:
                self.robot.stop_robot()
                decision = "CRITICAL: NO SAFE EXIT PROFILE FOUND"
        else:
            self.robot.move_forward()
            decision = "NOMINAL EXPLORATION SPEED ENGAGED"

        return {
            "Mission": mission,
            "Status": status_report["Status"],
            "Decision": decision,
            "Warnings": status_report["Warnings"],
            "Zone": self.analyzer.analyze_temperature()
        }


# --- UI RENDERING & GRAPHICS ENGINE ---
def run_feature_simulation():
    pygame.init()
    screen = pygame.display.set_mode((1150, 600))
    pygame.display.set_caption("Asteria Advanced Feature Verification Simulator")
    clock = pygame.time.Clock()
    font_mono = pygame.font.SysFont("Courier", 14, bold=True)

    # Boot components
    rover = AsteriaConfig("Asteria-02", 400, 300)
    env = Environment()
    brain = AsteriaBrain(rover, env)

    while True:
        # Check window events or manual keyboard parameter testing shifts
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Manual parameter environment simulation testing hooks (Arrow Keys)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]: env.temperature += 2      # Increase temperature dynamically
        if keys[pygame.K_DOWN]: env.temperature -= 2    # Drop temperature dynamically
        if keys[pygame.K_r]: rover.battery = 100.0       # 'R' key manual hot recharger cell injection

        # Execute system software updates
        telemetry = brain.run_cycle()
        rover.update_position()

        # Canvas Draw Architecture
        screen.fill((8, 10, 16))

        # 1. Background Spatial Grid Mesh Matrix
        for x in range(0, 800, 40):
            pygame.draw.line(screen, (16, 22, 34), (x, 0), (x, 600), 1)
        for y in range(0, 600, 40):
            pygame.draw.line(screen, (16, 22, 34), (0, y), (800, y), 1)
        pygame.draw.rect(screen, (46, 59, 84), (0, 0, 800, 600), 3)

        # 2. Render Fading Breadcrumb Trace Memory Path
        for idx, pt in enumerate(rover.distance_history):
            alpha_ratio = int((idx / len(rover.distance_history)) * 255)
            marker_surf = pygame.Surface((4, 4))
            marker_surf.set_alpha(alpha_ratio)
            marker_surf.fill((0, 255, 180))
            screen.blit(marker_surf, (pt[0]-2, pt[1]-2))

        # 3. Draw Terrain Map Obstacles
        for obs_x, obs_y, r in env.obstacles:
            pygame.draw.circle(screen, (36, 24, 24), (obs_x, obs_y), r)
            pygame.draw.circle(screen, (110, 48, 48), (obs_x, obs_y), r, 2)
            pygame.draw.circle(screen, (180, 70, 70), (obs_x, obs_y), r - 5, 1)

        # 4. Draw Interactive Lidar Sensor Beams (Raycast Visualization)
        rad_f = math.radians(rover.angle)
        rad_l = math.radians(rover.angle - 45)
        rad_r = math.radians(rover.angle + 45)
        rad_b = math.radians(rover.angle + 180)

        pygame.draw.line(screen, (0, 210, 255), (rover.x, rover.y), (rover.x + rover.distance * math.cos(rad_f), rover.y + rover.distance * math.sin(rad_f)), 1)
        pygame.draw.line(screen, (0, 120, 220), (rover.x, rover.y), (rover.x + rover.distance_left * math.cos(rad_l), rover.y + rover.distance_left * math.sin(rad_l)), 1)
        pygame.draw.line(screen, (0, 120, 220), (rover.x, rover.y), (rover.x + rover.distance_right * math.cos(rad_r), rover.y + rover.distance_right * math.sin(rad_r)), 1)
        pygame.draw.line(screen, (100, 60, 150), (rover.x, rover.y), (rover.x + rover.distance_rear * math.cos(rad_b), rover.y + rover.distance_rear * math.sin(rad_b)), 1)# 5. Draw Rover Unit Core Framerover_poly = [(rover.x + 16 * math.cos(rad_f), rover.y + 16 * math.sin(rad_f)),(rover.x + 11 * math.cos(rad_f + 2.4), rover.y + 11 * math.sin(rad_f + 2.4)),(rover.x + 11 * math.cos(rad_f - 2.4), rover.y + 11 * math.sin(rad_f - 2.4))]pygame.draw.polygon(screen, (0, 255, 140), rover_poly)pygame.draw.circle(screen, (255, 255, 255), (int(rover.x), int(rover.y)), 3)# 6. Build the Integrated Control Room Analytics HUD Displaypygame.draw.rect(screen, (12, 15, 24), (800, 0, 350, 600))pygame.draw.line(screen, (0, 255, 140), (800, 0), (800, 600), 2)# Color routing conditions for risk levelsstatus_colors = {"SAFE": (0, 255, 120), "RISKY": (255, 190, 0), "DANGER": (255, 40, 40)}stat_color = status_colors.get(telemetry("Status"), (255, 255, 255))# Populate structured output panels lineshud_lines = [("====== MAIN SOFTWARE REGISTER ======", (40, 180, 255)),(f"Active Task Vector  : {telemetry('Mission')}", (255, 255, 255)),(f"Safety Level State  : {telemetry('Status')}", stat_color),(f"Core Decision Output: {telemetry('Decision')}", (255, 255, 255)),("-" * 34, (50, 70, 100)),("====== ENVIRONMENT payload ANALYZER ======", (40, 180, 255)),(f"Planetary Category  : {telemetry('Zone')}", (0, 210, 255)),(f"Ambient Temperature : {env.temperature} K  (Use Up/Down)", (255, 255, 255)),(f"Luminosity Threshold: {env.luminosity} lux", (255, 255, 255)),("-" * 34, (50, 70, 100)),("====== HARDWARE SUBSYSTEMS REG ======", (40, 180, 255)),(f"Onboard Battery Cell: {rover.battery:.2f}%  (Press 'R' to Fill)", (0, 255, 120) if rover.battery > 20 else (255, 40, 40)),(f"Drive Velocity Mag  : {rover.speed} m/s", (255, 255, 255)),(f"Orientation Angle   : {rover.angle}°", (255, 255, 255)),("-" * 34, (50, 70, 100)),("====== LOGGED TELEMETRY HARDWARE ARRAYS ======", (40, 180, 255)),(f"Lidar Sensor F: {int(rover.distance)} cm", (255, 255, 255)),(f"Lidar Sensor L: {int(rover.distance_left)} cm", (255, 255, 255)),(f"Lidar Sensor R: {int(rover.distance_right)} cm", (255, 255, 255)),(f"Lidar Sensor B: {int(rover.distance_rear)} cm", (255, 255, 255)),]for i, (txt, col) in enumerate(hud_lines):screen.blit(font_mono.render(txt, True, col), (815, 20 + (i * 24)))# 7. Render Floating Software Warning Alerts Block Matrixpygame.draw.rect(screen, (20, 24, 38), (815, 490, 320, 95))pygame.draw.rect(screen, (60, 70, 90), (815, 490, 320, 95), 1)screen.blit(font_mono.render("ACTIVE RISK FLAGS MATRIX:", True, (160, 180, 210)), (825, 496))if telemetry("Warnings"):for offset, alert in enumerate(telemetry("Warnings")(:3)):screen.blit(font_mono.render(f"!! {alert}", True, (255, 70, 70)), (825, 520 + (offset * 20)))else:screen.blit(font_mono.render("NO ACTIVE FAULTS FOUND", True, (0, 255, 120)), (825, 530))pygame.display.flip()clock.tick(60)if name == "main":run_feature_simulation()