import pygame
import random
import math
import sys
from asteria_core import (
    AsteriaConfig, Environment, EnvironmentAnalyzer, CoveragePlanner,
    AsteriaBrain, MissionController, Memory,
)

# Display Viewport Parameters
# WIDTH/HEIGHT are placeholders until SimulationEngine.__init__ queries the
# actual monitor resolution and switches into fullscreen mode - every other
# module-level reference to these (PlanetaryObstacle.draw, HUD.draw, etc.)
# reads them at call time, so updating the globals before the game loop
# starts is enough to make the whole simulation fullscreen-aware.
WIDTH, HEIGHT = 1150, 700
FPS = 60
TILE_SIZE = 50

# The world has no fixed size any more. Terrain and obstacles are
# generated on demand in square chunks around wherever the robot
# currently is, and unloaded again once they fall out of range, so the
# rover can roam indefinitely in any direction.
CHUNK_TILES = 16                      # tiles per chunk side
CHUNK_SIZE = CHUNK_TILES * TILE_SIZE  # world units per chunk
CHUNK_LOAD_RADIUS = 3                 # chunks kept generated around the robot
SPAWN_CLEARANCE = 200                 # keep the area around spawn obstacle-free

# Size (in chunks) of a single biome "region". Biomes are placed on a
# coarser grid than chunks and blended with smoothstep interpolation, so
# terrain drifts gradually from one biome into the next as the robot
# travels instead of flipping abruptly at a chunk boundary.
BIOME_MACRO_CELL = 6.0

# High-fidelity Mars Palette Vectors
WHITE = (245, 245, 250)
BLACK = (12, 14, 20)
RED = (255, 70, 70)
BLUE = (0, 160, 255)
GREEN = (0, 255, 140)
GRAY = (75, 80, 95)
PANEL_BG = (22, 22, 30)

# ---------------------------------------------------------------------
# Biome definitions. Each biome gives the terrain its own tile palette,
# its own obstacle mix (density / crater vs. rock ratio / size range),
# and a baseline ambient temperature that the environment drifts toward
# while the rover is inside it. This is what makes the world feel
# different in different places instead of being one uniform surface
# repeated forever.
# ---------------------------------------------------------------------
BIOMES = {
    "rust_plains": {
        "label": "Rust Plains",
        "palette": [(165, 78, 45), (130, 58, 30), (195, 105, 65)],
        "obstacles_per_chunk": 8,
        "crater_chance": 0.5,
        "obstacle_size": (15, 50),
        "base_temperature": 210,
    },
    "basalt_flats": {
        "label": "Basalt Flats",
        "palette": [(70, 66, 68), (48, 45, 47), (95, 90, 92)],
        "obstacles_per_chunk": 4,
        "crater_chance": 0.25,
        "obstacle_size": (15, 35),
        "base_temperature": 195,
    },
    "highland_ridges": {
        "label": "Highland Ridges",
        "palette": [(150, 95, 60), (110, 68, 40), (185, 130, 90)],
        "obstacles_per_chunk": 13,
        "crater_chance": 0.2,
        "obstacle_size": (20, 55),
        "base_temperature": 165,
    },
    "crater_field": {
        "label": "Crater Field",
        "palette": [(140, 70, 40), (100, 48, 25), (170, 95, 55)],
        "obstacles_per_chunk": 16,
        "crater_chance": 0.85,
        "obstacle_size": (25, 60),
        "base_temperature": 200,
    },
    "polar_frost": {
        "label": "Polar Frost",
        "palette": [(190, 175, 175), (150, 140, 145), (215, 205, 210)],
        "obstacles_per_chunk": 3,
        "crater_chance": 0.35,
        "obstacle_size": (12, 30),
        "base_temperature": 130,
    },
}
# Ordering used to walk the [0, 1) noise value across the biome list.
BIOME_ORDER = ["polar_frost", "highland_ridges", "rust_plains", "crater_field", "basalt_flats"]


class MartianTile:
    def __init__(self, tile_type, size, rng, palette):
        self.tile_type = tile_type
        self.size = size
        self.color = palette[tile_type]

        # Uses the chunk's own rng (instead of reseeding the global random
        # module per-tile, which the old fixed-grid version did) so tile
        # detail is deterministic per world coordinate without disturbing
        # unrelated randomness elsewhere (obstacle placement, events, etc).
        self.dust_grains = [(rng.randint(2, size - 4), rng.randint(2, size - 4)) for _ in range(4)]
        self.iron_vein = (rng.randint(0, size), rng.randint(0, size), rng.randint(0, size), rng.randint(0, size))

    def draw(self, screen, x, y, camera_x, camera_y):
        rect = pygame.Rect(x * self.size - camera_x, y * self.size - camera_y, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)

        border_color = tuple(max(0, c - 5) for c in self.color)
        pygame.draw.rect(screen, border_color, rect, 1)

        for dx, dy in self.dust_grains:
            pygame.draw.circle(screen, (95, 38, 18), (rect.x + dx, rect.y + dy), 1)

        pygame.draw.line(screen, (110, 48, 22), (rect.x + self.iron_vein[0], rect.y + self.iron_vein[1]),
                          (rect.x + self.iron_vein[2], rect.y + self.iron_vein[3]), 1)


class PlanetaryObstacle:
    def __init__(self, x, y, radius, is_crater=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.is_crater = is_crater

    def draw(self, screen, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        if -self.radius < sx < WIDTH - 250 and -self.radius < sy < HEIGHT:
            if self.is_crater:
                pygame.draw.circle(screen, (85, 38, 18), (int(sx), int(sy)), self.radius)
                pygame.draw.circle(screen, (135, 60, 32), (int(sx), int(sy)), self.radius, 3)
                pygame.draw.circle(screen, (60, 25, 10), (int(sx), int(sy)), self.radius - 4, 1)
            else:
                pygame.draw.circle(screen, (55, 60, 70), (int(sx), int(sy)), self.radius)
                pygame.draw.circle(screen, (85, 90, 105), (int(sx), int(sy)), self.radius, 2)
                pygame.draw.circle(screen, (40, 44, 52), (int(sx), int(sy)), self.radius - 5)


class SimulationRover:
    """Handles lidar sensing and rendering. Movement itself lives in
    AsteriaConfig (asteria_core) so the on-screen rover uses the same
    dodge-and-return + coverage-sweep logic as the core simulation."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.sensor_range = 150
        self.trail_history = []
        self.active_beams = [150] * 4

    def cast_lidar_rays(self, obstacles):
        # No world edge to hit any more - a beam only stops on an obstacle
        # or at its maximum sensor range.
        offsets = [0, -90, 90, 180]
        distances = [self.sensor_range] * 4

        for i, offset in enumerate(offsets):
            rad = math.radians(self.angle + offset)
            for step in range(5, self.sensor_range, 3):
                tx = self.x + step * math.cos(rad)
                ty = self.y + step * math.sin(rad)
                hit = False
                for obs in obstacles:
                    if math.hypot(tx - obs.x, ty - obs.y) <= obs.radius:
                        distances[i] = step
                        hit = True
                        break
                if hit: break
        self.active_beams = distances
        return distances

    def sync_from_config(self, config):
        """Pull position/heading from AsteriaConfig, which now owns movement
        (including the dodge-and-return maneuver)."""
        self.x = config.x
        self.y = config.y
        self.angle = config.heading % 360

        if not self.trail_history or math.hypot(self.x - self.trail_history[-1][0], self.y - self.trail_history[-1][1]) > 8:
            self.trail_history.append((self.x, self.y))
            if len(self.trail_history) > 80:
                self.trail_history.pop(0)

    def draw(self, screen, camera_x, camera_y):
        sx, sy = self.x - camera_x, self.y - camera_y

        offsets = [0, -90, 90, 180]
        for i, offset in enumerate(offsets):
            rad_beam = math.radians(self.angle + offset)
            dist = self.active_beams[i]
            tx = sx + dist * math.cos(rad_beam)
            ty = sy + dist * math.sin(rad_beam)
            beam_color = RED if dist < 30 else (0, 210, 255)
            pygame.draw.line(screen, beam_color, (sx, sy), (tx, ty), 1)
            pygame.draw.circle(screen, beam_color, (int(tx), int(ty)), 3)

        for idx, pt in enumerate(self.trail_history):
            px, py = pt[0] - camera_x, pt[1] - camera_y
            if 0 < px < WIDTH - 250 and 0 < py < HEIGHT:
                alpha = int((idx / len(self.trail_history)) * 180)
                trail_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                trail_surface.fill((80, 30, 10, alpha))
                screen.blit(trail_surface, (px - 3, py - 3))

        rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        cos_p, sin_p = math.cos(rad + math.pi / 2), math.sin(rad + math.pi / 2)

        wheel_offsets = [(12, 12), (0, 12), (-12, 12), (12, -12), (0, -12), (-12, -12)]
        for wx, wy in wheel_offsets:
            cx = sx + (wx * cos_a + wy * cos_p)
            cy = sy + (wx * sin_a + wy * sin_p)
            wheel_surf = pygame.Surface((11, 5), pygame.SRCALPHA)
            wheel_surf.fill((45, 45, 50))
            rot_wheel = pygame.transform.rotate(wheel_surf, -self.angle)
            screen.blit(rot_wheel, rot_wheel.get_rect(center=(int(cx), int(cy))).topleft)

        points = [
            (sx + 16 * cos_a, sy + 16 * sin_a),
            (sx - 12 * cos_a + 10 * cos_p, sy - 12 * sin_a + 10 * sin_p),
            (sx - 12 * cos_a - 10 * cos_p, sy - 12 * sin_a - 10 * sin_p)
        ]
        pygame.draw.polygon(screen, (235, 240, 245), points)
        pygame.draw.polygon(screen, (140, 150, 165), points, 2)

        pygame.draw.circle(screen, (20, 60, 140), (int(sx - 3 * cos_a), int(sy - 3 * sin_a)), 6)
        pygame.draw.circle(screen, (40, 110, 240), (int(sx - 3 * cos_a), int(sy - 3 * sin_a)), 6, 1)


class HUD:
    # Number of text rows the panel below prints per frame. Kept as a
    # constant (rather than measured after the fact) so the row spacing
    # and font size can be sized to fit BEFORE the first frame renders.
    ROW_COUNT = 36

    def __init__(self):
        # Fullscreen resolutions vary a lot (a laptop's 768px-tall panel
        # needs tighter spacing than a 1440p monitor), so figure out how
        # much vertical room each row actually gets and scale the font
        # and line spacing to it. This guarantees every telemetry row is
        # visible regardless of the monitor the sim ends up running on,
        # rather than assuming a fixed 700px window like before.
        top_margin, bottom_margin = 25, 20
        available = max(HEIGHT - top_margin - bottom_margin, self.ROW_COUNT * 10)
        self.row_height = max(10, min(20, available // self.ROW_COUNT))

        if self.row_height >= 16:
            font_size = 14
        elif self.row_height >= 13:
            font_size = 12
        else:
            font_size = 10

        self.font = pygame.font.SysFont("Courier", font_size, bold=True)

    def draw(self, screen, config, analyzer, coverage_planner, biome_label, brain_status, memory):
        panel_x = WIDTH - 250
        pygame.draw.rect(screen, PANEL_BG, (panel_x, 0, 250, HEIGHT))
        pygame.draw.line(screen, GREEN, (panel_x, 0), (panel_x, HEIGHT), 2)

        status_color = {
            "SAFE": GREEN,
            "RISKY": (255, 200, 0),
            "DANGER": RED,
        }.get(brain_status["Status"], WHITE)

        # Show at most one warning line at a time so the panel doesn't
        # overflow when several fire on the same cycle; the count makes
        # it clear when more are being suppressed.
        warnings = brain_status["Warnings"]
        warning_line = warnings[0] if warnings else "None"
        if len(warnings) > 1:
            warning_line += f" (+{len(warnings) - 1} more)"

        hud_elements = [
            ("== ORIGINAL CONFIG REG ==", (0, 180, 255)),
            (f"Robot Name : {config.robot_name}", WHITE),
            (f"Wheel Rad  : {config.wheel_radius} cm", WHITE),
            (f"Wheel Base : {config.wheel_base} cm", WHITE),
            ("-" * 22, GRAY),
            ("== CORE DRIVE TELEMETRY ==", (0, 180, 255)),
            (f"Active Cmd : {config.direction}", (255, 215, 0) if config.direction != "Forward" else GREEN),
            (f"Dodge St.  : {config.dodge_state}", RED if config.dodge_state else GREEN),
            (f"Heading    : {config.heading:.1f} deg", WHITE),
            (f"Max Speed  : {config.max_speed} cm/s", WHITE),
            (f"Is Moving  : {config.is_moving}", GREEN if config.is_moving else RED),
            (f"Braking St : {config.braking}", RED if config.braking else WHITE),
            (f"Battery Cell: {config.battery:.1f}%", GREEN if config.battery > 25 else RED),
            ("-" * 22, GRAY),
            ("== MISSION BRAIN ==", (0, 180, 255)),
            (f"Mission    : {brain_status['Mission']}", (255, 200, 120)),
            (f"Risk Status: {brain_status['Status']}", status_color),
            (f"Decision   : {brain_status['Decision']}", WHITE),
            (f"Warning    : {warning_line}", status_color if warnings else WHITE),
            (f"Experiences: {len(memory.experience_log)} logged", (0, 210, 255)),
            ("-" * 22, GRAY),
            ("== COVERAGE SWEEP ==", (0, 180, 255)),
            (f"Progress   : {coverage_planner.progress():.1f}%", GREEN),
            (f"Waypoint   : {coverage_planner.index}/{len(coverage_planner.waypoints)}", WHITE),
            ("-" * 22, GRAY),
            ("== PAYLOAD SCANNERS ==", (0, 180, 255)),
            (f"Biome      : {biome_label}", (255, 200, 120)),
            (f"Classification: {analyzer.analyze_temperature()}", GREEN),
            (f"Core Thermal : {analyzer.environment.temperature:.1f} K", WHITE),
            (" (Hold Up/Down Key)", (140, 155, 170)),
            ("-" * 22, GRAY),
            ("== LOGGED DISTANCE REG ==", (0, 180, 255)),
            (f"Front Lidar : {int(config.distance) if config.distance else 0} cm", WHITE),
            (f"Left Lidar  : {int(config.distance_left) if config.distance_left else 0} cm", WHITE),
            (f"Right Lidar : {int(config.distance_right) if config.distance_right else 0} cm", WHITE),
            (f"Rear Lidar  : {int(config.distance_rear) if config.distance_rear else 0} cm", WHITE),
            ("-" * 22, GRAY),
            ("[ESC] Quit", (140, 155, 170)),
        ]

        for idx, (text, color) in enumerate(hud_elements):
            screen.blit(self.font.render(text, True, color), (panel_x + 12, 25 + (idx * self.row_height)))


class SimulationEngine:
    def __init__(self):
        pygame.init()

        # Query the monitor's native resolution and switch the whole sim
        # into fullscreen at that size. Every other module-level use of
        # WIDTH/HEIGHT (obstacle culling, camera centering, the HUD panel
        # rect) reads these globals at call time, so rebinding them here -
        # before anything else touches the screen - is enough to make the
        # entire simulation, including the telemetry panel, fullscreen.
        global WIDTH, HEIGHT
        display_info = pygame.display.Info()
        WIDTH, HEIGHT = display_info.current_w, display_info.current_h

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Asteria Advanced Exploration Core")
        self.clock = pygame.time.Clock()
        self.hud = HUD()

        # World is unbounded: terrain and obstacles are generated in
        # chunks on demand around wherever the robot currently is, and
        # chunks that fall out of range get unloaded again. world_seed
        # just gives this run's terrain (and biome layout) its own flavor
        # while keeping each chunk's contents deterministic (so
        # re-visiting a spot within the same run always looks the same).
        self.world_seed = random.randint(0, 1_000_000)
        self.tile_chunks = {}        # (chunk_x, chunk_y) -> 2D list of MartianTile
        self.obstacle_chunks = {}    # (chunk_x, chunk_y) -> list of PlanetaryObstacle
        self.chunk_biomes = {}       # (chunk_x, chunk_y) -> biome key
        self.obstacles = []          # flattened obstacles from currently loaded chunks

        spawn_x, spawn_y = 0.0, 0.0
        self.sim_robot = SimulationRover(spawn_x, spawn_y)
        self.camera_x, self.camera_y = 0, 0

        # AsteriaConfig owns position/heading/movement, including the
        # dodge-and-return obstacle maneuver.
        self.config = AsteriaConfig("Asteria-02", 20)
        self.config.x = spawn_x
        self.config.y = spawn_y
        self.config.heading = 0.0
        self.config.move_step = 2.0     # matches the rover's old forward speed
        self.config.turn_step = 4.0     # matches the rover's old turn rate (per frame)

        # Tracks how many consecutive frames the rover hasn't moved, so we
        # can force it loose if it's genuinely boxed in by obstacles.
        self._last_pos = (self.config.x, self.config.y)
        self._stuck_frames = 0

        self.environment = Environment()
        self.analyzer = EnvironmentAnalyzer(self.environment)

        # These were defined in asteria_core but never actually wired into
        # the pygame simulation - the engine was calling config.avoid_obstacles()
        # directly every frame, skipping straight past risk assessment,
        # mission selection, and experience logging entirely. Routing every
        # frame through AsteriaBrain.run_cycle() (below, in step()) restores
        # all three: overall_status() actually decides SAFE/RISKY/DANGER,
        # MissionController actually switches missions in response, and
        # Memory actually logs an experience whenever something noteworthy
        # happens.
        self.memory = Memory()
        self.mission_controller = MissionController()

        # Current biome the robot is standing in, plus a manual thermal
        # offset (Up/Down keys nudge this) layered on top of the biome's
        # own ambient baseline.
        self.current_biome = "rust_plains"
        self.temperature_offset = 0.0

        # Still gives the rover a long-range heading to work toward so it
        # sweeps systematically rather than wandering aimlessly - it just
        # isn't a hard boundary any more.
        self.coverage_planner = CoveragePlanner(width=20000, height=20000, lane_spacing=250)

        # AsteriaConfig already implements every method AsteriaBrain expects
        # from "robot" (x/y, heading, path_heading, steer_toward, is_dodging,
        # avoid_obstacles, change_speed, stop_robot) so self.config can be
        # handed to the brain directly - no adapter needed.
        self.brain = AsteriaBrain(
            self.analyzer, self.config, self.mission_controller,
            self.memory, self.coverage_planner,
        )
        self.last_brain_result = {"Mission": "Explore", "Status": "SAFE", "Decision": "Standby", "Warnings": []}

        self._refresh_loaded_chunks()
        self._update_current_biome()

    # ---------------------------------------------------------------
    # Biome layout (smooth macro-scale noise over chunk coordinates)
    # ---------------------------------------------------------------
    def _macro_rng(self, mx, my):
        # A separate spatial hash from the per-chunk one, on a coarser
        # grid, so biome regions span many chunks instead of flipping
        # every chunk.
        seed = (self.world_seed + mx * 668265263 + my * 374761393) & 0xFFFFFFFF
        return random.Random(seed)

    def _biome_noise(self, cx, cy):
        """Smooth value noise in [0, 1) sampled at chunk coordinates,
        interpolated between random values pinned to a coarser macro
        grid so the result changes gradually as (cx, cy) moves."""
        gx, gy = cx / BIOME_MACRO_CELL, cy / BIOME_MACRO_CELL
        x0, y0 = math.floor(gx), math.floor(gy)
        fx, fy = gx - x0, gy - y0

        def corner(ix, iy):
            return self._macro_rng(ix, iy).random()

        v00, v10 = corner(x0, y0), corner(x0 + 1, y0)
        v01, v11 = corner(x0, y0 + 1), corner(x0 + 1, y0 + 1)

        sx = fx * fx * (3 - 2 * fx)   # smoothstep, avoids grid-aligned seams
        sy = fy * fy * (3 - 2 * fy)
        top = v00 + (v10 - v00) * sx
        bottom = v01 + (v11 - v01) * sx
        return top + (bottom - top) * sy

    def _biome_for_chunk(self, cx, cy):
        value = self._biome_noise(cx, cy)
        idx = min(int(value * len(BIOME_ORDER)), len(BIOME_ORDER) - 1)
        return BIOME_ORDER[idx]

    def _update_current_biome(self):
        cx, cy = self._chunk_coord(self.config.x, self.config.y)
        self.current_biome = self.chunk_biomes.get((cx, cy), self._biome_for_chunk(cx, cy))

        # Drift the environment's temperature toward this biome's ambient
        # baseline (plus whatever manual offset Up/Down has applied) so the
        # payload scanners actually read differently as the rover crosses
        # into a new region, rather than staying fixed all game long.
        target = BIOMES[self.current_biome]["base_temperature"] + self.temperature_offset
        self.environment.temperature += (target - self.environment.temperature) * 0.02

    # ---------------------------------------------------------------
    # Chunk-based infinite world generation
    # ---------------------------------------------------------------
    def _chunk_coord(self, x, y):
        return (math.floor(x / CHUNK_SIZE), math.floor(y / CHUNK_SIZE))

    def _chunk_rng(self, cx, cy):
        # A cheap, explicit spatial hash rather than relying on Python's
        # tuple-hashing behaviour, so chunk generation is deterministic
        # and reproducible regardless of interpreter/version quirks.
        seed = (self.world_seed + cx * 73856093 + cy * 19349663) & 0xFFFFFFFF
        return random.Random(seed)

    def _generate_tile_chunk(self, cx, cy):
        rng = self._chunk_rng(cx, cy)
        biome = self.chunk_biomes.setdefault((cx, cy), self._biome_for_chunk(cx, cy))
        palette = BIOMES[biome]["palette"]
        grid = [
            [MartianTile(rng.choice([0, 0, 1, 2]), TILE_SIZE, rng, palette) for _ in range(CHUNK_TILES)]
            for _ in range(CHUNK_TILES)
        ]
        self.tile_chunks[(cx, cy)] = grid

    def _generate_obstacle_chunk(self, cx, cy):
        rng = self._chunk_rng(cx, cy)
        biome = self.chunk_biomes.setdefault((cx, cy), self._biome_for_chunk(cx, cy))
        params = BIOMES[biome]
        min_size, max_size = params["obstacle_size"]

        chunk_obstacles = []
        for _ in range(params["obstacles_per_chunk"]):
            ox = cx * CHUNK_SIZE + rng.uniform(0, CHUNK_SIZE)
            oy = cy * CHUNK_SIZE + rng.uniform(0, CHUNK_SIZE)
            if math.hypot(ox, oy) < SPAWN_CLEARANCE:
                continue  # keep the spawn area clear
            is_crater = rng.random() < params["crater_chance"]
            size = rng.randint(min_size, max_size)
            chunk_obstacles.append(PlanetaryObstacle(ox, oy, size, is_crater))
        self.obstacle_chunks[(cx, cy)] = chunk_obstacles

    def _refresh_loaded_chunks(self):
        """Ensure every chunk within CHUNK_LOAD_RADIUS of the robot exists,
        drop chunks that fell out of range, and rebuild the flat obstacle
        list used for lidar/collision this frame."""
        center_cx, center_cy = self._chunk_coord(self.config.x, self.config.y)
        needed = {
            (center_cx + dx, center_cy + dy)
            for dx in range(-CHUNK_LOAD_RADIUS, CHUNK_LOAD_RADIUS + 1)
            for dy in range(-CHUNK_LOAD_RADIUS, CHUNK_LOAD_RADIUS + 1)
        }

        for key in needed:
            if key not in self.chunk_biomes:
                self.chunk_biomes[key] = self._biome_for_chunk(*key)
            if key not in self.tile_chunks:
                self._generate_tile_chunk(*key)
            if key not in self.obstacle_chunks:
                self._generate_obstacle_chunk(*key)

        for key in list(self.tile_chunks.keys()):
            if key not in needed:
                del self.tile_chunks[key]
        for key in list(self.obstacle_chunks.keys()):
            if key not in needed:
                del self.obstacle_chunks[key]
        for key in list(self.chunk_biomes.keys()):
            if key not in needed:
                del self.chunk_biomes[key]

        self.obstacles = [o for chunk in self.obstacle_chunks.values() for o in chunk]

    # ---------------------------------------------------------------
    # Camera / steering / recovery
    # ---------------------------------------------------------------
    def update_viewport_camera(self):
        # The world has no edges, so the camera never needs clamping - it
        # always keeps the robot exactly centered, which means the robot
        # itself can never drift out of frame.
        self.camera_x = self.sim_robot.x - (WIDTH - 250) / 2
        self.camera_y = self.sim_robot.y - HEIGHT / 2

    def emergency_unstick(self):
        """Last resort: if the rover hasn't moved in a while (genuinely boxed
        in, e.g. by overlapping obstacles), push it directly away from the
        nearest obstacle instead of relying on sensor-based turning. This
        guarantees the rover never freezes permanently."""
        nearest, nearest_dist = None, None
        for obs in self.obstacles:
            d = math.hypot(self.config.x - obs.x, self.config.y - obs.y)
            if nearest_dist is None or d < nearest_dist:
                nearest_dist, nearest = d, obs

        if nearest is not None and nearest_dist > 0:
            away_heading = math.degrees(math.atan2(self.config.y - nearest.y, self.config.x - nearest.x))
        else:
            # Nothing nearby to push off of - there's no map center to
            # retreat toward any more, so just turn around.
            away_heading = (self.config.heading + 180) % 360

        self.config.heading = away_heading
        self.config.x += 6 * math.cos(math.radians(away_heading))
        self.config.y += 6 * math.sin(math.radians(away_heading))
        self.config.dodge_state = None
        self.config.dodge_direction = None
        print(f"{self.config.robot_name} emergency unstick "
              f"-> pos=({self.config.x:.1f},{self.config.y:.1f})")

    def run_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Fullscreen has no window chrome to close from, so give
                    # the player an explicit, discoverable way out.
                    running = False
            self.step()
            self.clock.tick(FPS)
        pygame.quit()

    def step(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.temperature_offset += 1
        if keys[pygame.K_DOWN]:
            self.temperature_offset -= 1

        # Make sure terrain/obstacles exist wherever the robot currently
        # is - the world has no fixed size, so chunks are generated (and
        # unloaded) on demand as the robot roams.
        self._refresh_loaded_chunks()

        # Recompute which biome the robot is standing in and drift the
        # environment's temperature toward that biome's baseline - this is
        # what makes conditions actually change as the robot travels.
        self._update_current_biome()

        # Keep the sensing/rendering rover in sync with the config's
        # current position before casting rays this frame.
        self.sim_robot.sync_from_config(self.config)

        # 1. Cast active telemetry sweeps
        beams = self.sim_robot.cast_lidar_rays(self.obstacles)

        # 2. Feed sensor readings into the core config + environment
        self.config.update_distance(beams[0])
        self.config.update_distance_left(beams[1])
        self.config.update_distance_right(beams[2])
        self.config.update_distance_rear(beams[3])

        self.environment.update_front_distance(beams[0])
        self.environment.update_left_distance(beams[1])
        self.environment.update_right_distance(beams[2])
        self.environment.update_rear_distance(beams[3])

        # 3. Movement runs unconditionally every frame - exactly like before
        #    the mission/risk layer existed - so the rover can never stall
        #    out just because a particular decision string (e.g. "Proceed
        #    Carefully" with a capital C, or "Return to charging station")
        #    wasn't wired to an action in AsteriaBrain.execute_decision().
        #    The mission/risk/experience system still runs every frame and
        #    still logs to memory - it just no longer gates whether the
        #    robot actually moves.
        self.brain.steer_toward_coverage_target()
        status = self.analyzer.overall_status()
        mission = self.mission_controller.choose_mission(status, self.config.battery)
        decision = self.brain.make_decision(status, mission)
        if self.brain.should_save_experience(status, decision):
            self.memory.save_experience()

        self.config.avoid_obstacles()
        self.config.brakes()
        self.config.remember_distance()

        self.last_brain_result = {
            "Mission": mission,
            "Status": status["Status"],
            "Warnings": status["Warnings"],
            "Decision": decision,
        }

        # Slow, steady power draw while moving so battery actually depletes
        # over a play session and the "Recharge" mission gets exercised;
        # while that mission is active the rover trickle-charges instead of
        # draining further (it keeps exploring regardless - see above).
        if mission == "Recharge":
            self.config.battery = min(100.0, self.config.battery + 0.4)
        elif self.config.is_moving and self.config.battery > 0:
            self.config.consume_power(0.015)

        # If the rover hasn't actually moved for a while, it's genuinely
        # boxed in (e.g. overlapping obstacles) - force it loose rather
        # than let it freeze indefinitely.
        moved = math.hypot(self.config.x - self._last_pos[0], self.config.y - self._last_pos[1])
        if moved < 0.05:
            self._stuck_frames += 1
        else:
            self._stuck_frames = 0
        self._last_pos = (self.config.x, self.config.y)

        if self._stuck_frames > 20:
            self.emergency_unstick()
            self._stuck_frames = 0
            self._last_pos = (self.config.x, self.config.y)

        # 4. Pull the updated position/heading back into the rover for
        #    rendering, then re-center the camera on it.
        self.sim_robot.sync_from_config(self.config)
        self.update_viewport_camera()

        # 5. Render only the tiles currently inside the viewport.
        self.screen.fill(BLACK)
        start_tile_x = math.floor(self.camera_x / TILE_SIZE)
        end_tile_x = math.floor((self.camera_x + WIDTH - 250) / TILE_SIZE) + 1
        start_tile_y = math.floor(self.camera_y / TILE_SIZE)
        end_tile_y = math.floor((self.camera_y + HEIGHT) / TILE_SIZE) + 1

        for ty in range(start_tile_y, end_tile_y):
            for tx in range(start_tile_x, end_tile_x):
                chunk_key = (tx // CHUNK_TILES, ty // CHUNK_TILES)
                grid = self.tile_chunks.get(chunk_key)
                if grid is None:
                    continue  # chunk not loaded (shouldn't normally happen in-view)
                local_x = tx % CHUNK_TILES
                local_y = ty % CHUNK_TILES
                grid[local_y][local_x].draw(self.screen, tx, ty, self.camera_x, self.camera_y)

        for obs in self.obstacles:
            obs.draw(self.screen, self.camera_x, self.camera_y)

        self.sim_robot.draw(self.screen, self.camera_x, self.camera_y)
        biome_label = BIOMES[self.current_biome]["label"]
        self.hud.draw(self.screen, self.config, self.analyzer, self.coverage_planner,
                       biome_label, self.last_brain_result, self.memory)

        pygame.display.update()


if __name__ == "__main__":
    SimulationEngine().run_loop()