class RobotConfig:
    def __init__(self, robot_name, max_speed):
        self.robot_name = robot_name
        self.wheel_radius = 20
        self.max_speed = max_speed
        self.wheel_base = 30
        self.battery = 100
    def show_config(self):
        print(f"Robot name: {self.robot_name}")
        print(f"Wheel radius: {self.wheel_radius}")
        print(f"Maximum speed: {self.max_speed}")
        print(f"Wheel Base: {self.wheel_base}")
        print(f"Battery percentage is {self.battery}")
    def change_speed(self,new_speed):
        self.max_speed = new_speed
    def stop_robot(self):
        self.max_speed = 0
        print(f"{self.robot_name}  has stopped")
    def consume_power(self,amount):
        self.battery -= amount
        if self.battery > 0:
            return self.batttery
        else:
            self.battery = 0
            return "Battery Depleted"
asteria = RobotConfig("Asteria",100)
asteria.consume_power(40)
asteria.change_speed(150)
asteria.stop_robot()
asteria.show_config()
