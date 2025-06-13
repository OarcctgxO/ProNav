import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_VIDEODRIVER"] = "windows"
import warnings

warnings.filterwarnings(
    "ignore", category=UserWarning, message="pkg_resources is deprecated"
)
import pygame
from pygame.locals import *
import math

LAND_IMAGE = None
from bodies import *
from const import *
import laws

# Инициализация Pygame
pygame.init()
WIDTH, HEIGHT = 1600, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.SCALED)
LAND_IMAGE = pygame.image.load("land.png").convert()
pygame.display.set_caption("Ракетная симуляция")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Impact", 20)
# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
DEEPSKYBLUE = (0, 191, 255)


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
        # Смещение относительно самолета
        dx = pos[0] - self.airplane.x
        dy = pos[1] - self.airplane.y

        # Вычисляем угол поворота
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

        # Применяем масштаб
        sx = dx_rot * self.scale
        sy = dy_rot * self.scale

        # Центрируем самолет и переворачиваем Y-ось
        screen_x = WIDTH // 2 + sx
        screen_y = HEIGHT // 2 - sy

        return (int(screen_x), int(screen_y))

    def screen_to_world(self, pos):
        sx, sy = pos
        # Переводим экранные координаты в относительные
        dx_rot = (sx - WIDTH // 2) / self.scale
        dy_rot = (HEIGHT // 2 - sy) / self.scale  # учтём инверсию Y

        vx, vy = self.airplane.vx, self.airplane.vy
        speed = math.hypot(vx, vy)
        if speed < eps:
            # Без поворота
            dx = dx_rot
            dy = dy_rot
        else:
            # Вычисляем компоненты поворота
            cos_alpha = vy / speed
            sin_alpha = vx / speed
            # Обратное преобразование поворота
            dx = dx_rot * cos_alpha + dy_rot * sin_alpha
            dy = -dx_rot * sin_alpha + dy_rot * cos_alpha

        # Возвращаем абсолютные мировые координаты
        x = self.airplane.x + dx
        y = self.airplane.y + dy
        return (x, y)

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
        self.airplane.ax = 0
        self.airplane.ay = 0

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

        # Сохраняем траекторию
        self.trajectory.append(
            ((self.airplane.x, self.airplane.y), (self.missile.x, self.missile.y))
        )
        if len(self.trajectory) > 2000:
            self.trajectory.pop(0)

        # Проверка коллизий
        distance = hypot(
            self.missile.x - self.airplane.x, self.missile.y - self.airplane.y
        )
        if distance < 0.1:
            self.game_over = True

        # Проверка победы
        if hypot(self.airplane.x, self.airplane.y) < 1.0:
            self.win = True
            self.game_over = True

    def draw_direction_arrow(
        self,
        surface,
        color,
        target_pos,
        arrow_length=20,
        arrow_head_size=5,
        line_width=2,
    ):
        # Получаем размеры экрана
        screen_width, screen_height = WIDTH, HEIGHT

        # Центр экрана
        center_x, center_y = screen_width // 2, screen_height // 2
        center_pos = (center_x, center_y)

        # Координаты цели
        target_x, target_y = target_pos

        # Вектор направления
        dir_x = target_x - center_x
        dir_y = target_y - center_y

        # Нормализуем вектор (приводим к длине 1)
        distance = math.hypot(dir_x, dir_y)
        if distance > 0:
            norm_x = dir_x / distance
            norm_y = dir_y / distance
        else:
            norm_x, norm_y = 0, 0  # Если цель в центре - не рисуем стрелку

        # Конечная точка стрелки
        end_x = center_x + norm_x * arrow_length
        end_y = center_y + norm_y * arrow_length
        end_pos = (end_x, end_y)

        # Рисуем линию стрелки
        pygame.draw.line(surface, color, center_pos, end_pos, line_width)

        # Если стрелка достаточно длинная, рисуем наконечник
        if distance > 0:
            # Угол наклона стрелки
            angle = math.atan2(dir_y, dir_x)

            # Точки для треугольника наконечника
            arrow_points = [
                end_pos,
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

    def draw(self):
        screen.fill(BLACK)
        
        # Всегда вычисляем границы видимой области
        screen_corners = [(0, 0), (WIDTH, 0), (WIDTH, HEIGHT), (0, HEIGHT)]
        world_corners = [self.screen_to_world(corner) for corner in screen_corners]
        min_x = min(corner[0] for corner in world_corners)
        max_x = max(corner[0] for corner in world_corners)
        min_y = min(corner[1] for corner in world_corners)
        max_y = max(corner[1] for corner in world_corners)

        if LAND_IMAGE:
            # Рассчитываем угол поворота земли (противоположный направлению самолета)
            vx, vy = self.airplane.vx, self.airplane.vy
            speed = math.hypot(vx, vy)
            if speed < eps:
                angle_deg = 0
            else:
                # Угол в радианах (относительно положительного направления X)
                angle_rad = -math.atan2(vy, vx)
                # Преобразуем в градусы и добавляем 90 градусов, чтобы верх земли был севером (положительное Y)
                angle_deg = math.degrees(angle_rad) + 90
            
            # Масштабируем изображение земли с учетом мирового масштаба
            # Размер земли в мировых координатах: 1000x1000
            world_size = 1000
            pixel_size = int(world_size * self.scale)
            scaled_land = pygame.transform.smoothscale(LAND_IMAGE, (pixel_size, pixel_size))
            
            # Поворачиваем изображение земли
            rotated_land = pygame.transform.rotate(scaled_land, angle_deg)
            
            # Позиционируем землю так, чтобы ее центр (0,0) совпадал с зеленой зоной победы
            land_rect = rotated_land.get_rect()
            center_pos = self.world_to_screen((0, 0))
            land_rect.center = center_pos
            
            # Рисуем землю
            screen.blit(rotated_land, land_rect)
        
        # Остальной код отрисовки остается без изменений...
        # Отрисовка зоны победы
        center = self.world_to_screen((0, 0))
        radius = int(1 * self.scale)
        pygame.draw.circle(screen, GREEN, center, radius, 2)

        # Вертикальные линии сетки
        start_kx = math.floor(min_x / grid_size)
        end_kx = math.ceil(max_x / grid_size)
        for k in range(start_kx, end_kx + 1):
            x = k * grid_size
            start_point = (x, min_y)
            end_point = (x, max_y)
            start_screen = self.world_to_screen(start_point)
            end_screen = self.world_to_screen(end_point)
            # pygame.draw.line(screen, (200, 200, 200), start_screen, end_screen, 1)

        # Горизонтальные линии сетки
        start_ky = math.floor(min_y / grid_size)
        end_ky = math.ceil(max_y / grid_size)
        for k in range(start_ky, end_ky + 1):
            y = k * grid_size
            start_point = (min_x, y)
            end_point = (max_x, y)
            start_screen = self.world_to_screen(start_point)
            end_screen = self.world_to_screen(end_point)
            # pygame.draw.line(screen, (200, 200, 200), start_screen, end_screen, 1)


        # Отрисовка траекторий
        if len(self.trajectory) > 1:
            # Подготовка точек для самолета (синие)
            air_points = [self.world_to_screen(a_pos) for a_pos, _ in self.trajectory]
            pygame.draw.lines(screen, BLUE, False, air_points, 2)

            # Подготовка точек для ракеты (красные)
            miss_points = [self.world_to_screen(m_pos) for _, m_pos in self.trajectory]
            pygame.draw.lines(screen, RED, False, miss_points, 2)

        self.draw_direction_arrow(screen, GREEN, self.world_to_screen((0, 0)))
        self.draw_direction_arrow(
            screen, RED, self.world_to_screen((self.missile.x, self.missile.y))
        )

        # Отрисовка объектов
        a_pos = self.world_to_screen((self.airplane.x, self.airplane.y))
        m_pos = self.world_to_screen((self.missile.x, self.missile.y))
        pygame.draw.circle(screen, BLUE, a_pos, 6)
        pygame.draw.circle(screen, RED, m_pos, 6)

        # Отрисовка текста
        texts = [
            f"Закон наведения: {self.current_law.__name__}",
            "[1-6] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[AD] - управление самолетом",
        ]
        y = 10
        for text in texts:
            surf = font.render(text, True, WHITE)
            screen.blit(surf, (10, y))
            y += 30

        txt_dist_win = (
            f"Расстояние до цели: {int(math.hypot(self.airplane.x, self.airplane.y))}"
        )
        txt_dist_mis = f"Расстояние до ракеты: {int(math.hypot(self.airplane.x - self.missile.x, self.airplane.y - self.missile.y))}"
        y = 10
        surf = font.render(txt_dist_win, True, GREEN)
        screen.blit(surf, (WIDTH - surf.get_width() - 10, y))
        y += 20
        surf = font.render(txt_dist_mis, True, RED)
        screen.blit(surf, (WIDTH - surf.get_width() - 10, y))

        if self.game_over:
            text = "Цель поражена!" if not self.win else "Победа!"
            color = RED if not self.win else GREEN
            surf = font.render(text, True, color)
            screen.blit(surf, (WIDTH // 2 - 160, HEIGHT // 2))

        pygame.display.flip()


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
