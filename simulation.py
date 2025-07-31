import arcade
from math import hypot

import bodies
import const
import laws


class Simulation:
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_fps = const.FPS
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
        self.airplane = bodies.Airplane(*const.airplane_start)
        self.missile = bodies.Missile(
            *const.missile_start, target=self.airplane, law=self.current_law, N=const.N
        )
        self.trajectory_aircraft = []
        self.trajectory_missile = []
        self.game_over = False
        self.win = False
        self.running = False

    def handle_input(self, keys):
        if arcade.key.A in keys and arcade.key.D in keys:
            self.airplane.an = 0.0
        elif arcade.key.A in keys:
            self.airplane.an = const.acceleration_n * abs(
                self.airplane.current_speed / const.airplane_max_speed
            )
        elif arcade.key.D in keys:
            self.airplane.an = -const.acceleration_n * abs(
                self.airplane.current_speed / const.airplane_max_speed
            )
        else:
            self.airplane.an = 0.0

        if arcade.key.W in keys and arcade.key.S in keys:
            self.airplane.at = 0.0
        elif arcade.key.W in keys:
            self.airplane.at = const.acceleration_t / 2
        elif arcade.key.S in keys:
            self.airplane.at = -const.acceleration_t
        else:
            self.airplane.at = 0.0
    def update(self, dt):
        if not self.running or self.paused or self.game_over:
            return
        self.airplane.calc_move(dt)
        self.missile.calc_move(dt)
        self.trajectory_aircraft.append(
            (
                self.airplane.x - self.airplane.vx * (const.move_trajectory / self.airplane.current_speed),
                self.airplane.y - self.airplane.vy * (const.move_trajectory / self.airplane.current_speed),
            )
        )
        self.trajectory_missile.append((self.missile.x, self.missile.y))
        if len(self.trajectory_aircraft) > 1000:
            self.trajectory_aircraft.pop(0)
            self.trajectory_missile.pop(0)

        if (
            hypot(self.missile.x - self.airplane.x, self.missile.y - self.airplane.y)
            < const.plane_size
        ):
            self.game_over = True

        if hypot(self.airplane.x, self.airplane.y) < const.win_zone_r:
            self.win = True
            self.game_over = True
