import random
import pygame


# Terrain types
GRASS = 0
SAND = 1
WATER = 2
ROCK = 3

        


class Tile:

    def __init__(self, tile_type, size):

        self.tile_type = tile_type
        self.size = size


        if tile_type == GRASS:
            self.color = (50, 170, 70)

        elif tile_type == SAND:
            self.color = (220, 200, 140)

        elif tile_type == WATER:
            self.color = (40, 120, 220)

        elif tile_type == ROCK:
            self.color = (120, 120, 120)



    def draw(self, screen, x, y, camera_x, camera_y):

        rect = pygame.Rect(
            x * self.size - camera_x,
            y * self.size - camera_y,
            self.size,
            self.size
        )


        # Base terrain
        pygame.draw.rect(
            screen,
            self.color,
            rect
        )


        # Small visual details

        if self.tile_type == GRASS:

            for _ in range(3):

                px = rect.x + random.randint(3, self.size-3)
                py = rect.y + random.randint(3, self.size-3)

                pygame.draw.circle(
                    screen,
                    (30,130,50),
                    (px,py),
                    2
                )


        elif self.tile_type == SAND:

            for _ in range(3):

                px = rect.x + random.randint(3, self.size-3)
                py = rect.y + random.randint(3, self.size-3)

                pygame.draw.circle(
                    screen,
                    (190,170,110),
                    (px,py),
                    1
                )


        elif self.tile_type == ROCK:

            pygame.draw.line(
                screen,
                (80,80,80),
                (rect.x+5, rect.y+5),
                (rect.x+self.size-5,
                 rect.y+self.size-5),
                2
            )


        elif self.tile_type == WATER:

            pygame.draw.line(
                screen,
                (120,200,255),
                (rect.x+5,
                 rect.y+self.size//2),
                (rect.x+self.size-5,
                 rect.y+self.size//2),
                2
            )





class World:

    def __init__(self, width=200, height=200, tile_size=29):

        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.temperature= 25
        self.luminosity=80
        self.humidity=40
        self.terrain = "Grass"

        self.tiles = []


        # Visual obstacles
        self.obstacles = []


        self.generate_world()

        self.generate_obstacles()



    def generate_world(self):

        for y in range(self.height):

            row = []


            for x in range(self.width):

                chance = random.random()


                if chance < 0.60:
                    terrain = GRASS

                elif chance < 0.75:
                    terrain = SAND

                elif chance < 0.90:
                    terrain = ROCK

                else:
                    terrain = WATER



                row.append(
                    Tile(
                        terrain,
                        self.tile_size
                    )
                )


            self.tiles.append(row)





    def generate_obstacles(self):

        for _ in range(50):

            x = random.randint(
                0,
                self.width-1
            )

            y = random.randint(
                0,
                self.height-1
            )


            obstacle = pygame.Rect(
                x*self.tile_size,
                y*self.tile_size,
                self.tile_size,
                self.tile_size
            )


            self.obstacles.append(obstacle)
        self.obstacles.append(pygame.Rect(800,650,self.tile_size,self.tile_size))
        




    # Future sensor use

    def get_tile(self, x, y):

        if x < 0 or y < 0:
            return None


        if x >= self.width or y >= self.height:
            return None


        return self.tiles[y][x]





    def draw(self, screen, camera_x, camera_y):


        # Draw terrain

        for y in range(self.height):

            for x in range(self.width):

                self.tiles[y][x].draw(
                    screen,
                    x,
                    y,
                    camera_x,
                    camera_y
                )



        # Draw obstacles

        for obstacle in self.obstacles:


            obstacle_rect = pygame.Rect(
                obstacle.x - camera_x,
                obstacle.y - camera_y,
                obstacle.width,
                obstacle.height
            )


            pygame.draw.rect(screen,(255,0,0),obstacle_rect)
            