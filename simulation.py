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

    def handle_input(self, keys):
        if arcade.key.SPACE in keys:
            self.running = not self.running
        if arcade.key.R in keys:
                self.reset()
                self.running = False
        if arcade.key.ESCAPE in keys:
            self.running = False
        if arcade.key.A in keys and arcade.key.D in keys:
            self.airplane.a = 0.0
        elif arcade.key.A in keys:
            self.airplane.a = acceleration_pressed
        elif arcade.key.D in keys:
            self.airplane.a = -acceleration_pressed
        else:
            self.airplane.a = 0.0
        if "MOUSE_UP" in keys:
            self.scale = np.clip(self.scale * 1.1, 1, 100)
        elif "MOUSE_DOWN" in keys:
            self.scale = np.clip(self.scale * 0.9, 1, 100)

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

    def get_data(self):
        render_data = {
            "airplane_pos": (self.airplane.x, self.airplane.y),
            "airplane_vel": (self.airplane.vx, self.airplane.vy),
            "missile_pos": (self.missile.x, self.missile.y),
            "missile_vel": (self.missile.vx, self.missile.vy),
            "trajectory": self.trajectory,
            "current_law_name": self.current_law.__name__,
            "distances": [
                f"Расстояние до цели: {int(hypot(self.airplane.x, self.airplane.y))}",
                f"Расстояние до ракеты: {int(hypot(self.airplane.x-self.missile.x, self.airplane.y-self.missile.y))}",
            ],
            "current_fps": self.current_fps,
            "game_over": self.game_over,
            "win": self.win,
            "scale": self.scale
        }
        
        return render_data