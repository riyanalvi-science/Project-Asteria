import random
import math


class AsteriaConfig:
    def __init__(self, robot_name, max_speed):
        self.robot_name = robot_name
        self.wheel_radius = 20
        self.max_speed = max_speed
        self.wheel_base = 30
        self.battery = 100
        self.is_moving = False
        self.distance = None
        self.temperature = None
        self.braking = False
        self.direction = None
        self.distance_right = None
        self.distance_left = None
        self.distance_rear = None
        self.distance_history = []

        # ---- NEW: position & heading, needed to "return to path" ----
        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0          # degrees, 0 = "original" forward direction
        self.path_heading = 0.0     # heading to steer back to once an obstacle is cleared
        self.move_step = 2.0        # distance covered per forward move
        self.turn_step = 15.0       # degrees turned per dodge/steer step

        # ---- NEW: dodge state machine (replaces "permanent turn") ----
        # None      -> cruising normally toward whatever heading it wants
        # "avoiding"-> actively steering away from an obstacle
        # "returning" -> obstacle cleared, steering heading back to path_heading
        self.dodge_state = None
        self.dodge_direction = None

    def show_config(self):
        print(f"Robot name: {self.robot_name}")
        print(f"Wheel radius: {self.wheel_radius}")
        print(f"Maximum speed: {self.max_speed}")
        print(f"Wheel Base: {self.wheel_base}")
        print(f"Battery percentage is {self.battery}")
        print(f"Robot is:{self.is_moving}")
        print(f"Robot state of motion {self.direction}")
        print(f"Position: ({self.x:.1f}, {self.y:.1f})  Heading: {self.heading:.1f}")

    def change_speed(self, new_speed):
        self.max_speed = new_speed
        if self.max_speed > 0:
            self.is_moving = True
        else:
            self.is_moving = False

    def stop_robot(self):
        self.max_speed = 0
        self.is_moving = False
        print(f"{self.robot_name} has stopped")

    def consume_power(self, amount):
        self.battery -= amount
        if self.battery > 0:
            return self.battery
        else:
            self.battery = 0
            print("Battery Depleted")
            return 0

    def update_distance(self, new_distance):
        self.distance = new_distance

    def update_distance_right(self, new_distance_right):
        self.distance_right = new_distance_right

    def update_distance_left(self, new_distance_left):
        self.distance_left = new_distance_left

    def update_distance_rear(self, new_distance_rear):
        self.distance_rear = new_distance_rear

    def can_move_forward(self):
        if self.distance is None:
            print("Front sensor data not available")
            return False
        return self.distance > 10

    def can_turn_right(self):
        if self.distance_right is None:
            print("Right sensor data not available")
            return False
        return self.distance_right > 10

    def can_turn_left(self):
        if self.distance_left is None:
            print("Left sensor data not available")
            return False
        return self.distance_left > 10

    def can_reverse(self):
        if self.distance_rear is None:
            print("Rear sensor data not available")
            return False
        return self.distance_rear > 10

    def brakes(self):
        if self.distance is None:
            self.braking = False
            return "Brakes not enabled"
        if self.distance < 10:
            self.braking = True
            self.stop_robot()
        else:
            self.braking = False

    # ---- helper: move the robot along its current heading ----
    def _advance_position(self, distance):
        # Standard math convention: heading 0 = +x axis, increasing clockwise
        # (matches pygame screen coordinates, where y grows downward).
        rad = math.radians(self.heading)
        self.x += distance * math.cos(rad)
        self.y += distance * math.sin(rad)

    def move_forward(self):
        if self.distance is None:
            print("Front sensor data not available")
        elif self.can_move_forward():
            self.direction = "Forward"
            self.max_speed = 20
            self.is_moving = True
            self._advance_position(self.move_step)
            print(f"{self.robot_name} is moving Forward "
                  f"-> pos=({self.x:.1f},{self.y:.1f}) heading={self.heading:.1f}")

    def turn_right(self):
        if self.distance_right is None:
            print("Right sensor data not available")
        elif self.can_turn_right():
            self.direction = "Right"
            self.max_speed = 20
            self.heading += self.turn_step
            print(f"{self.robot_name} is turning Right -> heading={self.heading:.1f}")
        else:
            self.braking = True
            self.stop_robot()
            print(f"{self.robot_name} cannot turn Right")

    def turn_left(self):
        if self.distance_left is None:
            print("Left sensor data not available")
        elif self.can_turn_left():
            self.direction = "Left"
            self.max_speed = 20
            self.heading -= self.turn_step
            print(f"{self.robot_name} is turning Left -> heading={self.heading:.1f}")
        else:
            self.braking = True
            self.stop_robot()
            print(f"{self.robot_name} cannot turn Left")

    def reverse(self):
        if self.distance_rear is None:
            print("Rear sensor data not available")
        elif self.can_reverse():
            self.direction = "Rear"
            self.max_speed = 20
            self._advance_position(-self.move_step)
            print(f"{self.robot_name} is moving backward")
        else:
            self.braking = True
            self.stop_robot()
            print(f"{self.robot_name} cannot move backward")

    def reverse_check_direction(self):
        if self.can_reverse():
            self.reverse()
        if self.distance is not None and self.distance > 25:
            self.braking = True
            self.stop_robot()
        else:
            print("Only rear path clear")

    # =========================================================
    #  DODGE-AND-RETURN OBSTACLE AVOIDANCE
    #  Instead of permanently changing direction, the robot
    #  remembers the heading it was travelling on (path_heading),
    #  steers around the obstacle, then steers back to it.
    # =========================================================
    def start_dodge(self):
        """Begin a dodge: remember current heading, pick a side to swing toward."""
        if self.dodge_state is not None:
            return  # already dodging
        #self.path_heading = self.heading
        if self.distance_left is not None and self.distance_right is not None:
            self.dodge_direction = "left" if self.distance_left >= self.distance_right else "right"
        elif self.can_turn_left():
            self.dodge_direction = "left"
        elif self.can_turn_right():
            self.dodge_direction = "right"
        else:
            self.dodge_direction = None
        self.dodge_state = "avoiding"
        print(f"{self.robot_name} starting dodge ({self.dodge_direction}), "
              f"remembering path_heading={self.path_heading:.1f}")

    def continue_dodge(self):
        """Advance the dodge state machine by one step."""
        if self.dodge_state == "avoiding":
            if self.dodge_direction == "left" and self.can_turn_left():
                self.heading -= self.turn_step
            elif self.dodge_direction == "right" and self.can_turn_right():
                self.heading += self.turn_step
            else:
                # chosen side is blocked too - try swapping to the other side
                # before resorting to reverse or giving up entirely.
                other = "right" if self.dodge_direction == "left" else "left"
                if other == "left" and self.can_turn_left():
                    self.dodge_direction = "left"
                    self.heading -= self.turn_step
                elif other == "right" and self.can_turn_right():
                    self.dodge_direction = "right"
                    self.heading += self.turn_step
                elif self.can_reverse():
                    self._advance_position(-self.move_step)
                    self.direction = "Dodge-reverse"
                    print(f"{self.robot_name} boxed in, reversing "
                          f"-> pos=({self.x:.1f},{self.y:.1f}) heading={self.heading:.1f}")
                    return
                else:
                    # fully boxed in on every side - abort the dodge instead of
                    # freezing forever, so the mission layer can stop/reassess.
                    self.dodge_state = None
                    self.dodge_direction = None
                    self.stop_robot()
                    print(f"{self.robot_name} is boxed in - aborting dodge")
                    return
            self._advance_position(self.move_step)
            self.direction = f"Dodge-{self.dodge_direction}"
            print(f"{self.robot_name} dodging {self.dodge_direction} "
                  f"-> pos=({self.x:.1f},{self.y:.1f}) heading={self.heading:.1f}")

            # once the front is clear again, start steering back to the original path
            if self.can_move_forward():
                self.dodge_state = "returning"

        elif self.dodge_state == "returning":
            diff = (self.path_heading - self.heading + 180) % 360 - 180
            if abs(diff) <= self.turn_step:
                self.heading = self.path_heading
                self.dodge_state = None
                self.dodge_direction = None
                print(f"{self.robot_name} realigned to original path "
                      f"heading={self.heading:.1f}")
            else:
                self.heading += self.turn_step if diff > 0 else -self.turn_step
            self._advance_position(self.move_step)
            self.direction = "Returning"
            print(f"{self.robot_name} returning to path "
                  f"-> pos=({self.x:.1f},{self.y:.1f}) heading={self.heading:.1f}")

    def is_dodging(self):
        return self.dodge_state is not None

    def steer_toward(self, target_heading):
        """Gradually rotate current heading toward target_heading (used while cruising,
        so the robot is always working toward its coverage waypoint, not just 'forward')."""
        diff = (target_heading - self.heading + 180) % 360 - 180
        if abs(diff) <= self.turn_step:
            self.heading = target_heading
        else:
            self.heading += self.turn_step if diff > 0 else -self.turn_step

    def avoid_obstacles(self):
        """Main obstacle-handling entry point: dodge temporarily, then resume the path."""
        if self.distance is None:
            print("Front sensor data not available")
            return
        if self.is_dodging():
            self.continue_dodge()
        elif self.distance < 10:
            self.start_dodge()
            self.continue_dodge()
        else:
            self.move_forward()

    def remember_distance(self, max_history=200):
        self.distance_history.append(self.distance)
        if len(self.distance_history) > max_history:
            self.distance_history.pop(0)


class Environment:
    def __init__(self):
        self.temperature = 25
        self.luminosity = 80
        self.humidity = 50
        self.front_distance = 100
        self.rear_distance = 100
        self.right_distance = 100
        self.left_distance = 100

    def update_front_distance(self, v):
        self.front_distance = v

    def update_rear_distance(self, v):
        self.rear_distance = v

    def update_right_distance(self, v):
        self.right_distance = v

    def update_left_distance(self, v):
        self.left_distance = v

    def update_temperature(self, v):
        self.temperature = v

    def update_humidity(self, v):
        self.humidity = v

    def update_luminosity(self, v):
        self.luminosity = v

    def display_environment(self):
        print(f"______CURRENT ENVIRONMENT____\nFront Distance : {self.front_distance} cm\n"
              f"Rear Distance : {self.rear_distance} cm\nLeft Distance : {self.left_distance} cm\n"
              f"Right Distance : {self.right_distance} cm\nTemperature : {self.temperature} K\n"
              f"Humidity : {self.humidity} %\nLuminosity : {self.luminosity} lux")

    def reset_environment(self):
        self.temperature = None
        self.luminosity = None
        self.humidity = None
        self.front_distance = None
        self.rear_distance = None
        self.right_distance = None
        self.left_distance = None


class EnvironmentAnalyzer:
    def __init__(self, environment):
        self.environment = environment

    def analyze_temperature(self):
        t = self.environment.temperature
        if t is None:
            return "No readings available"
        elif t < 30:
            return "Deep space like"
        elif t < 150:
            return "Comet like"
        elif t < 273:
            return "Mars like"
        elif t < 310:
            return "Earth like"
        elif t < 330:
            return "Warm Earth like"
        elif t < 800:
            return "Venus like"
        elif t < 1000:
            return "Mercury Day-side like"
        elif t < 5800:
            return "Solar Surface like"
        elif t < 9000000:
            return "Solar Corona like"
        elif t < 15000000:
            return "Solar Core like"
        else:
            return "Temperature exceeds known limit"

    def analyze_luminosity(self):
        l = self.environment.luminosity
        if l is None:
            return "No readings available"
        elif l <= 0:
            return "Deep cave like"
        elif l < 1:
            return "Moonless night in the open sky"
        elif l < 10:
            return "Full moon night"
        elif l < 100:
            return "Twilight"
        elif l < 500:
            return "Laboratory"
        elif l < 10000:
            return "Overcast Earth"
        elif l < 100000:
            return "Earth at noon"
        elif l < 500000:
            return "Bright desert"
        elif l < 1000000:
            return "Mercury Surface"
        else:
            return "Near a bright star"

    def analyze_humidity(self):
        h = self.environment.humidity
        if h is None:
            return "Readings not available"
        elif h <= 0:
            return "Outer Space"
        elif h < 5:
            return "Interplanetary Space"
        elif h < 15:
            return "Atacama Desert"
        elif h < 30:
            return "Sahara Desert"
        elif h < 45:
            return "Heated indoor environment"
        elif h < 60:
            return "Typical Earth indoor environment"
        elif h < 75:
            return "Tropial Climate"
        elif h < 90:
            return "Rainforest"
        elif h < 100:
            return "Dense fog"
        else:
            return "Sensor malfunction"

    def _distance_label(self, d):
        if d is None:
            return "No reading available"
        elif d < 0:
            return "Invalid reading"
        elif d < 5:
            return "Collision Imminent"
        elif d < 15:
            return "Extremely Close"
        elif d < 30:
            return "Very Close"
        elif d < 60:
            return "Close"
        elif d < 100:
            return "Moderate Distance"
        elif d < 300:
            return "Clear Path"
        elif d < 1000:
            return "Open Area"
        else:
            return "Wide Open Area"

    def analyze_front_distance(self):
        return self._distance_label(self.environment.front_distance)

    def analyze_rear_distance(self):
        return self._distance_label(self.environment.rear_distance)

    def analyze_right_distance(self):
        return self._distance_label(self.environment.right_distance)

    def analyze_left_distance(self):
        return self._distance_label(self.environment.left_distance)

    def overall_status(self):
        warnings = []
        if self.environment.temperature is not None:
            if self.environment.temperature > 120:
                warnings.append("Critical thermal stress: extreme heat")
            elif self.environment.temperature < -150:
                warnings.append("Critical thermal stress: extreme cold")
            elif self.environment.temperature > 80:
                warnings.append("High temperature detected")
            elif self.environment.temperature < -100:
                warnings.append("Low temperature detected")
        if self.environment.front_distance is not None and self.environment.front_distance < 5:
            warnings.append("Immediate obstacle ahead")
        elif self.environment.front_distance is not None and self.environment.front_distance < 20:
            warnings.append("Object detected ahead")
        if self.environment.rear_distance is not None and self.environment.rear_distance < 5:
            warnings.append("Immediate obstacle behind")
        if self.environment.left_distance is not None and self.environment.left_distance < 5:
            warnings.append("Obstacle detected on left")
        if self.environment.right_distance is not None and self.environment.right_distance < 5:
            warnings.append("Obstacle detected on right")

        if len(warnings) == 0:
            return {"Status": "SAFE", "Warnings": []}
        elif len(warnings) == 1:
            return {"Status": "RISKY", "Warnings": warnings}
        else:
            return {"Status": "DANGER", "Warnings": warnings}


class EnvironmentSnapshot:
    def __init__(self, environment):
        self.front_distance = environment.front_distance
        self.rear_distance = environment.rear_distance
        self.right_distance = environment.right_distance
        self.left_distance = environment.left_distance
        self.temperature = environment.temperature
        self.humidity = environment.humidity
        self.luminosity = environment.luminosity


class Action:
    def __init__(self):
        self.action_name = None
        self.execution_time = None
        self.successful = None
        self.timestamp = None
        self.battery_used = None
        self.direction = None
        self.reason = None
        self.outcome = None


class Experience:
    def __init__(self):
        self.environment_before = None
        self.environment_after = None
        self.action = None
        self.outcome = None
        self.timestamp = None


class Memory:
    def __init__(self):
        self.last_environment = None
        self.previous_environment = None
        self.last_action = None
        self.previous_action = None
        self.last_outcome = None
        self.last_timestamp = None
        self.experience_log = []

    def remember_environment(self, environment):
        self.previous_environment = self.last_environment
        self.last_environment = EnvironmentSnapshot(environment)

    def remember_action(self, action):
        self.previous_action = self.last_action
        self.last_action = action

    def save_experience(self):
        experience = Experience()
        experience.environment_before = self.previous_environment
        experience.environment_after = self.last_environment
        experience.action = self.last_action
        experience.outcome = self.last_outcome
        experience.timestamp = self.last_timestamp
        self.experience_log.append(experience)

    def show_last_experience(self):
        if not self.experience_log:
            return "No experiences available"
        print(f"____Previous Experience____\n Initial conditions:{self.previous_environment}\n"
              f" Action taken:{self.last_action}\n Final conditions:{self.last_environment}")

    def reset_experience(self):
        self.previous_environment = None
        self.last_environment = None
        self.last_action = None


# =========================================================
#  COVERAGE PLANNING
#  Generates a boustrophedon ("lawnmower") sweep of waypoints
#  across a rectangular area so the robot systematically visits
#  the whole area rather than wandering wherever obstacles push it.
# =========================================================
class CoveragePlanner:
    def __init__(self, width, height, lane_spacing=10):
        self.width = width
        self.height = height
        self.lane_spacing = lane_spacing
        self.waypoints = self._generate_boustrophedon()
        self.index = 0

    def _generate_boustrophedon(self):
        waypoints = []
        y = 0.0
        going_right = True
        while y <= self.height:
            if going_right:
                waypoints.append((0.0, y))
                waypoints.append((self.width, y))
            else:
                waypoints.append((self.width, y))
                waypoints.append((0.0, y))
            y += self.lane_spacing
            going_right = not going_right
        return waypoints

    def current_target(self):
        if self.index >= len(self.waypoints):
            return None
        return self.waypoints[self.index]

    def advance_if_reached(self, x, y, threshold=3.0):
        target = self.current_target()
        if target is None:
            return
        dx, dy = target[0] - x, target[1] - y
        if (dx ** 2 + dy ** 2) ** 0.5 <= threshold:
            self.index += 1

    def is_complete(self):
        return self.index >= len(self.waypoints)

    def progress(self):
        if not self.waypoints:
            return 100.0
        return 100.0 * self.index / len(self.waypoints)

    @staticmethod
    def heading_to(x, y, target):
        """Heading (0 = +x axis, standard trig convention) from (x,y) to target."""
        dx, dy = target[0] - x, target[1] - y
        return math.degrees(math.atan2(dy, dx)) % 360


class AsteriaBrain:
    def __init__(self, environment_analyzer, robot, mission_controller, memory, coverage_planner=None):
        self.environment_analyzer = environment_analyzer
        self.robot = robot
        self.mission_controller = mission_controller
        self.memory = memory
        self.coverage_planner = coverage_planner

    def evaluate_situation(self):
        status = self.environment_analyzer.overall_status()
        if status["Status"] == "SAFE":
            return "Continue Exploration"
        elif status["Status"] == "RISKY":
            return "Proceed with caution"
        else:
            return "Stop and reassess"

    def take_action(self):
        decision = self.evaluate_situation()
        if decision == "Continue Exploration":
            self.robot.avoid_obstacles()
        elif decision == "Proceed with caution":
            self.robot.change_speed(10)
            self.robot.avoid_obstacles()
        elif decision == "Stop and reassess":
            self.robot.stop_robot()

    def check_direction(self):
        if self.robot.can_turn_left():
            return "Turn left"
        elif self.robot.can_turn_right():
            return "Turn right"
        elif self.robot.can_reverse():
            return "Reverse"
        else:
            return "Stop: No safe direction available"

    def make_decision(self, status, mission):
        warnings = status["Warnings"]
        if mission == "Recharge":
            return "Return to charging station"
        elif mission == "Avoid Danger":
            return self.check_direction()
        elif mission == "Proceed Carefully":
            if status["Status"] == "RISKY":
                if "Obstacle detected on right" in warnings or "Object detected ahead" in warnings:
                    return self.check_direction()
                return "Proceed Carefully"
            return "Proceed Carefully"
        elif mission == "Explore":
            if status["Status"] == "SAFE":
                return "Move forward and continue exploration"
            elif status["Status"] == "RISKY":
                if "Object detected ahead" in warnings:
                    return self.check_direction()
                return "Proceed carefully"
            elif status["Status"] == "DANGER":
                if "Immediate obstacle ahead" in warnings:
                    return self.check_direction()
                return "Stop and reassess environment"
        return "Stop and wait"

    def execute_decision(self, decision):
        if decision in ("Turn left", "Turn right", "Reverse",
                        "Stop: No safe direction available"):
            # These are now handled through the dodge state machine so the
            # robot returns to its original heading afterwards, instead of
            # staying turned.
            self.robot.avoid_obstacles()
        elif decision == "Move forward and continue exploration":
            self.robot.avoid_obstacles()
        elif decision == "Proceed carefully":
            self.robot.change_speed(10)
            self.robot.avoid_obstacles()

    def steer_toward_coverage_target(self):
        """If a coverage plan exists and the robot isn't mid-dodge, point it at
        the next unvisited waypoint so, over time, it sweeps the whole area."""
        if self.coverage_planner is None or self.robot.is_dodging():
            return
        target = self.coverage_planner.current_target()
        if target is None:
            return
        desired_heading = CoveragePlanner.heading_to(self.robot.x, self.robot.y, target)
        self.robot.path_heading = desired_heading
        self.robot.steer_toward(desired_heading)
        self.coverage_planner.advance_if_reached(self.robot.x, self.robot.y)

    def run_cycle(self):
        self.steer_toward_coverage_target()
        status = self.environment_analyzer.overall_status()
        mission = self.mission_controller.choose_mission(status, self.robot.battery)
        decision = self.make_decision(status, mission)
        self.execute_decision(decision)
        if self.should_save_experience(status, decision):
            self.memory.save_experience()
        result = {
            "Mission": mission,
            "Status": status["Status"],
            "Warnings": status["Warnings"],
            "Decision": decision,
            "Battery": self.robot.battery,
            "Position": (round(self.robot.x, 1), round(self.robot.y, 1)),
            "Heading": round(self.robot.heading, 1),
            "Dodging": self.robot.dodge_state,
        }
        if self.coverage_planner is not None:
            result["Coverage %"] = round(self.coverage_planner.progress(), 1)
        return result

    def run(self, cycles):
        for _ in range(cycles):
            self.run_cycle()

    def should_save_experience(self, status, decision):
        if status["Status"] in ("DANGER", "RISKY"):
            return True
        return decision == "Stop and reassess"


class Mission:
    def __init__(self):
        self.name = None
        self.status = "Not Started"
        self.completed = False
        self.priority = "Normal"
        self.progress = None

    def start_mission(self):
        self.status = "Running"
        self.completed = False

    def complete_mission(self):
        self.status = "Completed"
        self.completed = True

    def abort_mission(self):
        pass


class MissionController:
    def __init__(self):
        self.current_mission = None

    def choose_mission(self, status, battery):
        if battery < 20:
            self.current_mission = "Recharge"
        elif status["Status"] == "DANGER":
            self.current_mission = "Avoid Danger"
        elif status["Status"] == "RISKY":
            self.current_mission = "Proceed Carefully"
        elif status["Status"] == "SAFE":
            self.current_mission = "Explore"
        else:
            self.current_mission = "Standby"
        return self.current_mission

    def update_mission(self, status, battery):
        if self.current_mission is None:
            self.choose_mission(status, battery)
        if self.current_mission == "Recharge":
            if battery == 100:
                self.current_mission = self.choose_mission(status, battery)
        elif self.current_mission == "Avoid Danger":
            if status["Status"] == "SAFE":
                self.current_mission = self.choose_mission(status, battery)
        elif self.current_mission == "Explore":
            if battery < 20 or status["Status"] == "DANGER":
                self.current_mission = self.choose_mission(status, battery)


class Simulation:
    def __init__(self, environment, brain):
        self.environment = environment
        self.brain = brain
        self.cycle = 0

    def generate_event(self):
        event = random.randint(1, 100)
        if event <= 70:
            pass
        elif event <= 85:
            self.environment.front_distance = random.randint(10, 30)
        elif event <= 95:
            self.environment.temperature = random.randint(80, 100)
        else:
            self.environment.luminosity = random.randint(0, 5)

    def next_cycle(self):
        self.cycle += 1
        self.generate_event()
        self.environment.temperature += random.randint(-5, 5)

        self.environment.front_distance += random.randint(-2, 2)
        if self.environment.front_distance < 0:
            self.environment.front_distance = 0
        self.environment.luminosity += random.uniform(-0.5, 0.5)
        if self.environment.luminosity < 0:
            self.environment.luminosity = 0
        self.environment.humidity += random.randint(-3, 3)
        if self.environment.humidity < 0:
            self.environment.humidity = 0
        self.environment.rear_distance += random.randint(-2, 2)
        if self.environment.rear_distance < 0:
            self.environment.rear_distance = 0
        self.environment.right_distance += random.randint(-2, 2)
        if self.environment.right_distance < 0:
            self.environment.right_distance = 0
        self.environment.left_distance += random.randint(-2, 2)
        if self.environment.left_distance < 0:
            self.environment.left_distance = 0

        self.brain.robot.update_distance(self.environment.front_distance)
        self.brain.robot.update_distance_left(self.environment.left_distance)
        self.brain.robot.update_distance_right(self.environment.right_distance)
        self.brain.robot.update_distance_rear(self.environment.rear_distance)

        result = self.brain.run_cycle()
        self.show_cycle(result)

    def run_simulation(self, cycles):
        for _ in range(cycles):
            self.next_cycle()
            if self.brain.coverage_planner is not None and self.brain.coverage_planner.is_complete():
                print(f"\n>>> Coverage complete after {self.cycle} cycles <<<")
                break

    def show_cycle(self, result):
        print("=" * 55)
        print("                 ASTERIA 1.0")
        print("=" * 55)
        print(f"Cycle      : {self.cycle}")
        print("\nMISSION")
        print("-" * 25)
        print(f"Mission    : {result['Mission']}")
        print(f"Status     : {result['Status']}")
        print(f"Decision   : {result['Decision']}")
        print("\nROBOT")
        print("-" * 25)
        print(f"Battery    : {self.brain.robot.battery}%")
        print(f"Position   : {result['Position']}   Heading: {result['Heading']}")
        print(f"Dodging    : {result['Dodging']}")
        if "Coverage %" in result:
            print(f"Coverage   : {result['Coverage %']}%")
        print("\nENVIRONMENT")
        print("-" * 25)
        print(f"Temperature: {self.environment.temperature} C")
        print(f"Humidity   : {self.environment.humidity} %")
        print(f"Luminosity : {self.environment.luminosity}")
        print(f"Front      : {self.environment.front_distance} m")
        print(f"Left       : {self.environment.left_distance} m")
        print(f"Right      : {self.environment.right_distance} m")
        print(f"Rear       : {self.environment.rear_distance} m")
        print("=" * 55)


class AsteriaTester:
    def __init__(self, simulation):
        self.simulation = simulation

    def test_safe_environment(self):
        e = self.simulation.environment
        e.temperature, e.front_distance = 25, 30
        e.left_distance, e.right_distance, e.rear_distance = 30, 30, 30
        e.humidity, e.luminosity = 40, 3
        self.simulation.next_cycle()

    def test_low_battery(self):
        self.simulation.brain.robot.battery = 15
        self.simulation.next_cycle()

    def test_obstacle_ahead(self):
        self.simulation.environment.front_distance = 2
        self.simulation.next_cycle()

    def run_all_tests(self):
        self.test_low_battery()
        self.test_obstacle_ahead()


if __name__ == "__main__":
    environment = Environment()
    environment_analyzer = EnvironmentAnalyzer(environment)
    memory = Memory()
    mission_controller = MissionController()
    robot = AsteriaConfig("Asteria", 50)

    # Plan a sweep over a 40x40 area with lanes 8 units apart -> full coverage
    coverage_planner = CoveragePlanner(width=40, height=40, lane_spacing=8)

    brain = AsteriaBrain(environment_analyzer, robot, mission_controller, memory, coverage_planner)
    simulation = Simulation(environment, brain)

    simulation.run_simulation(150)