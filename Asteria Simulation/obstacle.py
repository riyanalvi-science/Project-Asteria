import pygame
import random

from constants import *


class Obstacle:

    def __init__(self, x, y, obstacle_type):

        self.x = x
        self.y = y

        self.type = obstacle_type


        if obstacle_type == "ROCK":

            self.size = 30
            self.color = GRAY


        elif obstacle_type == "CRATER":

            self.size = 50
            self.color = (80, 80, 80)


        elif obstacle_type == "BOULDER":

            self.size = 40
            self.color = (100, 100, 100)


        else:

            self.size = 30
            self.color = BLACK



    def draw(self, screen, camera_x, camera_y):

        screen_x = self.x - camera_x

        screen_y = self.y - camera_y


        pygame.draw.circle(

            screen,

            self.color,

            (
                int(screen_x),
                int(screen_y)
            ),

            self.size

        )