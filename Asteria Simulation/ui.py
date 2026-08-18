import pygame


class UI:

    def __init__(self):

        self.font = pygame.font.SysFont(
            "arial",
            18
        )


        self.title_font = pygame.font.SysFont(
            "arial",
            26
        )



    def draw_text(self, screen, text, x, y):

        surface = self.font.render(
            text,
            True,
            (230,230,230)
        )

        screen.blit(
            surface,
            (x,y)
        )



    def draw_panel(self, screen, x, y, width, height):

        pygame.draw.rect(
            screen,
            (35,35,45),
            (x,y,width,height),
            border_radius=10
        )



    def draw(self, screen, robot, world,telemetry):


        # Right side panel

        panel_x = screen.get_width()-300


        self.draw_panel(
            screen,
            panel_x,
            20,
            280,
            500
        )



        # Title

        title = self.title_font.render(
            "ASTERIA",
            True,
            (0,200,255)
        )


        screen.blit(
            title,
            (panel_x+20,35)
        )



        # Robot information

        y = 90


        self.draw_text(
            screen,
            "ROBOT STATUS",
            panel_x+20,
            y
        )


        y+=35


        self.draw_text(
            screen,
            f"Position: {int(robot.x)}, {int(robot.y)}",
            panel_x+20,
            y
        )


        y+=25


        self.draw_text(
            screen,
            f"Speed: {robot.speed}",
            panel_x+20,
            y
        )


        y+=25


        self.draw_text(
            screen,
            f"Direction: {robot.angle} deg",
            panel_x+20,
            y
        )


        y+=50


        self.draw_text(
            screen,
            "ENVIRONMENT",
            panel_x+20,
            y
        )


        y+=35


        self.draw_text(
            screen,
            f"Temperature: {world.temperature} C",
            panel_x+20,
            y
        )


        y+=25


        self.draw_text(
            screen,
            f"Luminosity: {world.luminosity}",
            panel_x+20,
            y
        )


        y+=25


        self.draw_text(
            screen,
            "Terrain: Unknown",
            panel_x+20,
            y
        )

        y+=50
        self.draw_text(
            screen,
            "SENSOR DATA",
            panel_x+20,
            y
        )

        y += 35
        self.draw_text(
            screen,
            f"Front:{robot.front_distance}cm",
            panel_x+20,
            y
        )

        y += 25
        self.draw_text(
            screen,
            f"Rear:{robot.rear_distance}cm",
            panel_x+20,
            y
        )
        y += 25
        self.draw_text(
            screen,
            f"Left:{robot.left_distance}cm",
            panel_x+20,
            y
        )
        y+=25
        self.draw_text(
            screen,
            f"Right: {robot.right_distance}cm",
            panel_x+20,
            y
        )

        y +=25
        self.draw_text(screen,f"Zone:{telemetry['Zone']}",panel_x+20,y)
        y+=25
        self.draw_text(screen,f"Risk:{telemetry['Status']}",panel_x+20,y)