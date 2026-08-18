class RobotConfig:
    def __init__(self, robot_name, max_speed):
        self.robot_name = robot_name
        self.wheel_radius = 20
        self.max_speed = max_speed
        self.wheel_base = 30
        self.battery = 100
        self.is_moving= False
        self.distance= None
        self.temperature = None
        self.braking = False
        self.direction = None
        self.distance_right = None
        self.distance_left = None
        self.distance_rear = None
        self.distance_history = []
    def show_config(self):
        print(f"Robot name: {self.robot_name}")
        print(f"Wheel radius: {self.wheel_radius}")
        print(f"Maximum speed: {self.max_speed}")
        print(f"Wheel Base: {self.wheel_base}")
        print(f"Battery percentage is {self.battery}")
        print(f"Robot is:{self.is_moving}")
        print(f"Robot state of motion {self.direction}")
    def change_speed(self,new_speed):
        self.max_speed = new_speed
        if self.max_speed >0:
            self.is_moving=True 
        else:
             self.is_moving = False
    def stop_robot(self):
        self.max_speed = 0
        self.is_moving= False
        print(f"{self.robot_name} has stopped")
    def consume_power(self,amount):
        self.battery -= amount
        if self.battery > 0:
            return self.battery
        elif self.battery<=0:
            self.battery = 0
            print ("Battery Depleted")
            return 0
        else:
            print("Battery Depleted")
            return 0
    def update_distance(self,new_distance):
        self.distance = new_distance
    def update_distance_right(self,new_distance_right):
        self.distance_right = new_distance_right
    def update_distance_left(self,new_distance_left):
        self.distance_left = new_distance_left
    def update_distance_rear(self,new_distance_rear):
        self.distance_rear = new_distance_rear
    def can_move_forward(self):
        if self.distance is None:
            print("Front sensor data not available")
            return False
        elif self.distance>10:
            return True
        else:
            return False
    def can_turn_right(self):
        if self.distance_right is None:
           print("Right sensor data not available")
           return False
        if self.distance_right>10:
            return True
        else:
            return False
    def can_turn_left(self):
        if self.distance_left is None:
            print("Left sensor data not available")
            return False
        elif self.distance_left>10:
            return True
        else:
            return False
    def can_reverse(self):
        if self.distance_rear is None:
            print("Rear sensor data not available")
            return False
        if self.distance_rear>10:
            return True
        else:
            return False

    def brakes(self):
        if self.distance is None:
            self.braking = False
            return("Brakes not enabled")
        if self.distance<10:
            self.braking = True
            self.stop_robot()
        else:
            self.braking = False
    def move_forward(self):
        if self.distance is None:
            print("Front sensor data not available")
        elif self.can_move_forward() is True:
            self.direction = "Forward"
            self.max_speed = 20
            print("Asteria is moving Forward") 
    
    def turn_right(self):
        if self.distance_right is None:
            print("Right sensor data not available")
        elif self.can_turn_right() == True:
            self.direction = "Right"
            self.max_speed= 20
            print("Asteria is turning Right")
        else:
            self.braking = True
            self.stop_robot()
            print("Asteria cannot turn Right")
    def turn_left(self):
        if self.distance_left is None:
            print("Left sensor data not available")
        elif self.can_turn_left() == True:
            self.direction = "Left"
            self.max_speed= 20
            print("Asteria is turning Left")
        else:
            self.braking = True
            self.stop_robot()
            print("Asteria cannot turn Left")
    def reverse(self):
        if self.distance_rear is None:
            print("Rear sensor data not available")
        elif self.can_reverse():
            self.direction = "Rear"
            self.max_speed= 20
            print("Asteria is moving backward")
        else:
            self.braking = True
            self.stop_robot()
            print("Asteria cannot move backward")
    def reverse_check_direction(self):
        if self.can_reverse():
            self.reverse()
        if self.distance>25:
            self.braking = True
            self.stop_robot()
        else:
                print("Only rear path clear")

    def decide_direction(self):
        if self.can_turn_left() and self.can_turn_right():
                if self.distance_left>self.distance_right:
                    self.turn_left()
                elif self.distance_left == self.distance_right:
                    self.turn_left()
        elif self.can_turn_left():
            self.turn_left()
        elif self.can_turn_right():
            self.turn_right()
        else:
            self.reverse_check_direction()

    def avoid_obstacles(self):
        if self.distance == None:
            print("Front sensor data not available")
        elif self.distance<10:
            self.decide_direction()
        else:
            self.move_forward()
    def remember_distance(self):
        self.distance_history.append(self.distance)
    


asteria = RobotConfig("Asteria",100)
asteria.consume_power(40)
asteria.change_speed(150)
asteria.update_distance(10)
asteria.stop_robot()
asteria.show_config()
asteria.brakes()
asteria.move_forward()