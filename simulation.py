import arcade
from math import hypot
import numpy as np
from render import Renderer
from bodies import *
from const import *
import laws

class Simulation:
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_fps = FPS
        self.laws = {
            1: laws.PP,
            2: laws.TPN,
            3: laws.APN,
            4: laws.ZEMPN,
            5: laws.ZEMAPN,
            6: laws.myZEM,
        }
        self.current_law = laws.PP
        self.reset()

    def reset(self):
        self.airplane = airplane(*airplane_start)
        self.missile = missile(
            *missile_start, target=self.airplane, law=self.current_law, N=N
        )
        self.trajectory = []
        self.game_over = False
        self.win = False
        self.running = False

    def handle_input(self, keys):
        if arcade.key.A in keys and arcade.key.D in keys:
            self.airplane.a = 0.0
        elif arcade.key.A in keys:
            self.airplane.a = acceleration_pressed
        elif arcade.key.D in keys:
            self.airplane.a = -acceleration_pressed
        else:
            self.airplane.a = 0.0

    def update(self, dt):
        if not self.running or self.paused or self.game_over:
            return
        self.airplane.calc_move(dt)
        self.missile.calc_move(dt)
        self.trajectory.append(
            ((self.airplane.x, self.airplane.y), (self.missile.x, self.missile.y))
        )
        if len(self.trajectory) > 1000:
            self.trajectory.pop(0)

        if (
            hypot(
                self.missile.x - self.airplane.x, self.missile.y - self.airplane.y
            )
            < plane_size
        ):
            self.game_over = True

        if hypot(self.airplane.x, self.airplane.y) < win_zone_r:
            self.win = True
            self.game_over = True
