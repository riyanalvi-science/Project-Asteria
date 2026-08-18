import pygame

from constants import *


class Tile:

    def __init__(self, tile_type):

        self.tile_type = tile_type


        if tile_type == "GRASS":
            self.color = GREEN

        elif tile_type == "SAND":
            self.color = (194, 178, 128)

        elif tile_type == "ROCK":
            self.color = GRAY

        elif tile_type == "WATER":
            self.color = BLUE

        else:
            self.color = BLACK



    def draw(self, screen, x, y):

        pygame.draw.rect(
            screen,
            self.color,
            (
                x,
                y,
                TILE_SIZE,
                TILE_SIZE
            )
        )



class Terrain:

    def __init__(self):

        self.tiles = []


        self.generate()



    def generate(self):

        for row in range(MAP_HEIGHT):

            tile_row = []

            for col in range(MAP_WIDTH):

                if row < MAP_HEIGHT//3:

                    tile = Tile("SAND")

                elif row < (MAP_HEIGHT//3)*2:

                    tile = Tile("GRASS")

                else:

                    tile = Tile("ROCK")


                tile_row.append(tile)


            self.tiles.append(tile_row)



    def draw(self, screen, camera_x, camera_y):


        for row, tile_row in enumerate(self.tiles):

            for col, tile in enumerate(tile_row):


                x = (
                    col * TILE_SIZE
                    - camera_x
                )


                y = (
                    row * TILE_SIZE
                    - camera_y
                )


                tile.draw(
                    screen,
                    x,
                    y
                )