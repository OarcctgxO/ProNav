import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "windows"
import warnings

warnings.filterwarnings(
    "ignore", category=UserWarning, message="pkg_resources is deprecated"
)
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from bodies import *
from const import *
import laws

# Инициализация
pygame.init()
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.OPENGL)
LAND_IMAGE = pygame.image.load("land.png").convert_alpha()
pygame.display.set_caption("Ракетная симуляция")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Impact", 20)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)


class Simulation:
    def __init__(self):
        self.running = False
        self.paused = False
        self.laws = {
            K_1: laws.PP,
            K_2: laws.TPN,
            K_3: laws.APN,
            K_4: laws.ZEMPN,
            K_5: laws.ZEMAPN,
            K_6: laws.Hybrid,
        }
        self.current_law = laws.PP
        self.reset()
        self.init_gl()
        self.pygame_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def init_gl(self):
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glViewport(0, 0, WIDTH, HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, 0, HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        self.land_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.land_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        texture_data = pygame.image.tostring(LAND_IMAGE, "RGBA", 1)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            LAND_IMAGE.get_width(),
            LAND_IMAGE.get_height(),
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )

        self.interface_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )

    def reset(self):
        self.airplane = airplane(*airplane_start)
        self.missile = missile(
            *missile_start, target=self.airplane, law=self.current_law, N=N, alpha=alpha
        )
        self.trajectory = []
        self.keys_pressed = set()
        self.game_over = False
        self.win = False
        self.scale = scale

    def world_to_screen(self, pos):
        dx = pos[0] - self.airplane.x
        dy = pos[1] - self.airplane.y
        vx, vy = self.airplane.vx, self.airplane.vy
        speed = math.hypot(vx, vy)

        if speed < eps:
            dx_rot = dx
            dy_rot = dy
        else:
            beta = math.atan2(vy, vx)
            alpha = math.pi / 2 - beta
            dx_rot = dx * math.cos(alpha) - dy * math.sin(alpha)
            dy_rot = dx * math.sin(alpha) + dy * math.cos(alpha)

        sx = dx_rot * self.scale
        sy = dy_rot * self.scale
        return (WIDTH // 2 + int(sx), (HEIGHT // 2 - int(sy)))

    def draw_land(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        vx, vy = self.airplane.vx, self.airplane.vy
        speed = math.hypot(vx, vy)
        angle_deg = -math.degrees(math.atan2(vy, vx)) + 90 if speed > eps else 0

        glPushMatrix()
        glTranslatef(WIDTH // 2, HEIGHT // 2, 0)
        glRotatef(angle_deg, 0, 0, 1)
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-self.airplane.x, -self.airplane.y, 0)

        glBindTexture(GL_TEXTURE_2D, self.land_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(-500, -500)
        glTexCoord2f(1, 1)
        glVertex2f(500, -500)
        glTexCoord2f(1, 0)
        glVertex2f(500, 500)
        glTexCoord2f(0, 0)
        glVertex2f(-500, 500)
        glEnd()
        glPopMatrix()

    def draw_direction_arrow(
        self,
        surface,
        color,
        target_pos,
        arrow_length=20,
        arrow_head_size=5,
        line_width=2,
    ):
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        target_x, target_y = target_pos

        dir_x = target_x - center_x
        dir_y = target_y - center_y
        distance = math.hypot(dir_x, dir_y)

        if distance > 0:
            norm_x = dir_x / distance
            norm_y = dir_y / distance
        else:
            return

        end_x = center_x + norm_x * arrow_length
        end_y = center_y + norm_y * arrow_length

        pygame.draw.line(
            surface, color, (center_x, center_y), (end_x, end_y), line_width
        )

        angle = math.atan2(dir_y, dir_x)
        arrow_points = [
            (end_x, end_y),
            (
                end_x - arrow_head_size * math.cos(angle - math.pi / 6),
                end_y - arrow_head_size * math.sin(angle - math.pi / 6),
            ),
            (
                end_x - arrow_head_size * math.cos(angle + math.pi / 6),
                end_y - arrow_head_size * math.sin(angle + math.pi / 6),
            ),
        ]
        pygame.draw.polygon(surface, color, arrow_points)

    def draw_pygame_elements(self):
        self.pygame_surface.fill((0, 0, 0, 0))

        # Отрисовка зоны победы
        center = self.world_to_screen((0, 0))
        pygame.draw.circle(self.pygame_surface, GREEN, center, int(1 * self.scale), 2)

        # Отрисовка траекторий
        if len(self.trajectory) > 1:
            air_points = [self.world_to_screen(a_pos) for a_pos, _ in self.trajectory]
            pygame.draw.lines(self.pygame_surface, BLUE, False, air_points, 2)
            miss_points = [self.world_to_screen(m_pos) for _, m_pos in self.trajectory]
            pygame.draw.lines(self.pygame_surface, RED, False, miss_points, 2)

        a_pos = self.world_to_screen((self.airplane.x, self.airplane.y))
        m_pos = self.world_to_screen((self.missile.x, self.missile.y))

        # Отрисовка стрелок направления
        self.draw_direction_arrow(
            self.pygame_surface, GREEN, self.world_to_screen((0, 0))
        )
        self.draw_direction_arrow(self.pygame_surface, RED, m_pos)

        pygame.draw.circle(self.pygame_surface, BLUE, a_pos, 6)
        pygame.draw.circle(self.pygame_surface, RED, m_pos, 6)

        # Отрисовка текста (левая часть - управление)
        control_texts = [
            f"Закон наведения: {self.current_law.__name__}",
            "[1-6] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[AD] - управление самолетом",
        ]
        for i, text in enumerate(control_texts):
            text_surface = font.render(text, True, WHITE)
            self.pygame_surface.blit(text_surface, (10, 10 + i * 25))

        # Отрисовка текста (правая часть - расстояния)
        distance_texts = [
            f"Расстояние до цели: {int(math.hypot(self.airplane.x, self.airplane.y))}",
            f"Расстояние до ракеты: {int(math.hypot(self.airplane.x-self.missile.x, self.airplane.y-self.missile.y))}",
        ]
        for i, text in enumerate(distance_texts):
            color = GREEN if i == 0 else RED
            text_surface = font.render(text, True, color)
            self.pygame_surface.blit(
                text_surface, (WIDTH - text_surface.get_width() - 10, 10 + i * 25)
            )

        if self.game_over:
            text = "Цель поражена!" if not self.win else "Победа!"
            color = RED if not self.win else GREEN
            surf = font.render(text, True, color)
            self.pygame_surface.blit(
                surf, (WIDTH // 2 - surf.get_width() // 2, HEIGHT // 2)
            )

        # Обновляем текстуру интерфейса
        texture_data = pygame.image.tostring(self.pygame_surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            WIDTH,
            HEIGHT,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )

    def draw(self):
        self.draw_land()
        self.draw_pygame_elements()

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(0, 0)
        glTexCoord2f(1, 1)
        glVertex2f(WIDTH, 0)
        glTexCoord2f(1, 0)
        glVertex2f(WIDTH, HEIGHT)
        glTexCoord2f(0, 0)
        glVertex2f(0, HEIGHT)
        glEnd()

        pygame.display.flip()

    # Остальные методы остаются без изменений
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
            self.keys_pressed.add(event.key)
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
        if len(self.trajectory) > 2000:
            self.trajectory.pop(0)

        if (
            math.hypot(
                self.missile.x - self.airplane.x, self.missile.y - self.airplane.y
            )
            < 0.1
        ):
            self.game_over = True

        if math.hypot(self.airplane.x, self.airplane.y) < 1.0:
            self.win = True
            self.game_over = True


def main():
    sim = Simulation()
    running = True
    while running:
        dt = clock.tick(FPS) / sim_second

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            sim.handle_input(event)

        sim.update(dt)
        sim.draw()

    pygame.quit()


if __name__ == "__main__":
    main()
