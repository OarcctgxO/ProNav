import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "windows"
import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated")
import time
import pygame
import sys
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
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
            K_1: laws.PP,
            K_2: laws.TPN,
            K_3: laws.APN,
            K_4: laws.ZEMPN,
            K_5: laws.ZEMAPN,
            K_6: laws.ZEMbad,
        }
        self.current_law = laws.PP
        self.scale = scale
        
        # Инициализация рендерера
        pygame.init()
        self.width, self.height = 1920, 1080
        screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN)
        land_image = pygame.image.load("land.png").convert_alpha()
        pygame.display.set_caption("Ракетная симуляция")
        
        self.renderer = Renderer(self.width, self.height, land_image, self.scale)
        self.reset()

    def reset(self):
        self.airplane = airplane(*airplane_start)
        self.missile = missile(
            *missile_start, target=self.airplane, law=self.current_law, N=N, alpha=alpha
        )
        self.trajectory = []
        self.keys_pressed = set()
        self.game_over = False
        self.win = False

    def handle_input(self, event):
        if event.type == KEYDOWN:
            if event.key in self.laws:
                self.current_law = self.laws[event.key]
                self.reset()
                self.running = False
            if event.key == K_SPACE:
                self.running = not self.running
            if event.key == K_r:
                self.reset()
                self.running = False
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            self.keys_pressed.add(event.key)
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4:  # Колесо вверх
                self.scale = np.clip(self.scale * 1.1, 1, 100)
                self.renderer.set_scale(self.scale)
            elif event.button == 5:  # Колесо вниз
                self.scale = np.clip(self.scale * 0.9, 1, 100)
                self.renderer.set_scale(self.scale)
        elif event.type == KEYUP:
            if event.key in self.keys_pressed:
                self.keys_pressed.remove(event.key)

    def update_acceleration(self):
        self.airplane.a = 0
        if K_a in self.keys_pressed:
            self.airplane.a = acceleration_pressed
        if K_d in self.keys_pressed:
            self.airplane.a = -acceleration_pressed

    def update(self, dt):
        if not self.running or self.paused or self.game_over:
            return

        self.update_acceleration()
        self.airplane.calc_move(dt)
        self.missile.calc_move(dt)

        self.trajectory.append(
            ((self.airplane.x, self.airplane.y), (self.missile.x, self.missile.y))
        )
        if len(self.trajectory) > 1000:
            self.trajectory.pop(0)

        if (
            math.hypot(
                self.missile.x - self.airplane.x, self.missile.y - self.airplane.y
            )
            < plane_size
        ):
            self.game_over = True

        if math.hypot(self.airplane.x, self.airplane.y) < win_zone_r:
            self.win = True
            self.game_over = True

    def draw(self):
        # Подготавливаем данные для рендерера
        render_data = {
            "airplane_pos": (self.airplane.x, self.airplane.y),
            "airplane_vel": (self.airplane.vx, self.airplane.vy),
            "missile_pos": (self.missile.x, self.missile.y),
            "trajectory": self.trajectory,
            "current_law_name": self.current_law.__name__,
            "distances": [
                f"Расстояние до цели: {int(math.hypot(self.airplane.x, self.airplane.y))}",
                f"Расстояние до ракеты: {int(math.hypot(self.airplane.x-self.missile.x, self.airplane.y-self.missile.y))}",
            ],
            "current_fps": self.current_fps,
            "game_over": self.game_over,
            "win": self.win,
        }
        
        self.renderer.draw(render_data)

def main():
    sim = Simulation()
    running = True
    clock = pygame.time.Clock()
    target_fps = FPS

    while running:
        frame_start = time.time()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            sim.handle_input(event)

        dt = 1.0 / sim.current_fps
        sim.update(dt)
        sim.draw()

        frame_time = time.time() - frame_start
        if frame_time < 1.0 / target_fps:
            clock.tick(target_fps)
        else:
            sim.current_fps = 1.0 / frame_time

    pygame.quit()

if __name__ == "__main__":
    main()