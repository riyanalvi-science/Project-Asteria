import pygame
import math


class Robot:

    def __init__(self, x, y):

        # World position
        self.x = x
        self.y = y

        # Direction angle
        self.angle = 0
        

        # Visual size
        self.width = 60
        self.height = 45


        # Movement (temporary visualization)
        self.speed = 3


        # Sensor visualization
        self.sensor_range = 100
        self.front_distance=100
        self.left_distance=100
        self.right_distance=100
        self.rear_distance=100


    def move(self, keys):

        if keys[pygame.K_UP]:
            self.y -= self.speed
            self.angle = -90


        if keys[pygame.K_DOWN]:
            self.y += self.speed
            self.angle = 90


        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            self.angle = 180


        if keys[pygame.K_RIGHT]:
            self.x += self.speed
            self.angle = 0
        self.x= max(0,min(self.x,1600))
        self.y=max(0,min(self.y,1600))



    def draw(self, screen, camera_x, camera_y):

        # Convert world position to screen position

        robot_x = self.x - camera_x
        robot_y = self.y - camera_y



        # ==========================
        # Robot Shadow
        # ==========================

        shadow = pygame.Surface(
            (75,55),
            pygame.SRCALPHA
        )


        pygame.draw.ellipse(
            shadow,
            (0,0,0,80),
            (0,0,75,55)
        )


        screen.blit(
            shadow,
            (
                robot_x-37,
                robot_y-27
            )
        )



        # ==========================
        # Robot Body
        # ==========================

        body = pygame.Surface(
            (60,45),
            pygame.SRCALPHA
        )



        # Main chassis

        pygame.draw.rect(
            body,
            (160,165,175),
            (5,5,50,35),
            border_radius= 20
        )



        # Front bumper

        pygame.draw.rect(
            body,
            (80,85,95),
            (45,12,10,20),
            border_radius=4
        )



        # Camera housing

        pygame.draw.circle(
            body,
            (25,25,30),
            (30,10),
            7
        )



        # Camera lens

        pygame.draw.circle(
            body,
            (0,180,255),
            (30,10),
            3
        )



        # Left wheel

        pygame.draw.rect(
            body,
            (20,20,20),
            (5,8,8,30),
            border_radius=4
        )



        # Right wheel

        pygame.draw.rect(
            body,
            (20,20,20),
            (47,8,8,30),
            border_radius=4
        )



        # Battery panel

        pygame.draw.rect(
            body,
            (100,100,110),
            (20,28,20,5),
            border_radius=2
        )




        # Rotate body

        rotated = pygame.transform.rotate(
            body,
            -self.angle
        )



        rect = rotated.get_rect(
            center=(robot_x,robot_y)
        )


        screen.blit(
            rotated,
            rect
        )



        # ==========================
        # Sensor Ray
        # ==========================

        angle = math.radians(self.angle)



        sensor_x = robot_x + math.cos(angle)*self.sensor_range

        sensor_y = robot_y + math.sin(angle)*self.sensor_range



        pygame.draw.line(
            screen,
            (0,255,0),
            (robot_x,robot_y),
            (sensor_x,sensor_y),
            2
        )
    def execute_command(self,command):
        if command=="Forward":
            self.y -=self.speed
            self.angle = -90
        elif command == "Right":
            self.x+=self.speed
            self.angle=0
        elif command == "Left":
            self.x -= self.speed
            self.angle = 180
        elif command=="Rear":
            self.y += self.speed
            self.angle=90
        elif command =="STOP":
            pass
    def autonomous_move(self,direction):
        if direction == "FORWARD":
            self.y -= self.speed
        elif direction == "BACKWARD":
            self.y += self.speed
        elif direction == "LEFT":
            self.x -= self.speed
        elif direction == "RIGHT":
            self.x += self.speed
    # world boundary
        if self.x <= 0:
            direction = "RIGHT"
        elif self.x >= 4000:
            direction = "LEFT"
        elif self.y <= 0:
            direction = "BACKWARD"
        elif self.y >= 4000:
            direction = "FORWARD"