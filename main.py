# main_pygame.py
from os import environ
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from pygame.locals import *
import math
import sys
from bodies import *
from const import acceleration_pressed, FPS, sim_second, airplane_start, missile_start
import laws

# Инициализация Pygame
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ракетная симуляция")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

class Simulation:
    def __init__(self):
        self.running = False
        self.paused = False
        self.laws = {
            K_1: laws.PP,
            K_2: laws.TPN,
            K_3: laws.APN,
            K_4: laws.ZEMPN,
            K_5: laws.ZEMAPN
        }
        self.current_law = laws.PP
        self.reset()
        
    def reset(self):
        self.aircraft = airplane(*airplane_start)
        self.missile = missile(
            *missile_start,
            target=self.aircraft, law=self.current_law, N=3
        )
        self.trajectory = []
        self.keys_pressed = set()
        self.game_over = False
        self.win = False
        self.scale = 20  # Начальный масштаб
        self.offset_x = 0
        self.offset_y = 0
        
    def calculate_viewport(self):
        # Центрируем на самолете
        center_x = self.aircraft.x
        center_y = self.aircraft.y
        
        # Рассчитываем расстояние до центра
        distance_x = max(abs(center_x), abs(0))  # Учитываем (0,0)
        distance_y = max(abs(center_y), abs(0))
        
        # Определяем масштаб
        self.scale = min(
            800 / (2 * distance_x + 20),
            800 / (2 * distance_y + 20)
        )
        self.scale = 800 / 60
        # Смещение для центрирования
        self.offset_x = 400 - center_x * self.scale
        self.offset_y = 400 - center_y * self.scale

    def world_to_screen(self, pos):
        x = pos[0] * self.scale + self.offset_x
        y = 800 - (pos[1] * self.scale + self.offset_y)
        return (int(x), int(y))
        
    def handle_input(self, event):
        if event.type == KEYDOWN:
            if event.key in self.laws:
                self.current_law = self.laws[event.key]
                self.reset()
                self.running = not self.running
            if event.key == K_SPACE:
                self.running = not self.running
            if event.key == K_r:
                self.reset()
                self.running = not self.running
            self.keys_pressed.add(event.key)
            
        elif event.type == KEYUP:
            if event.key in self.keys_pressed:
                self.keys_pressed.remove(event.key)
                
    def update_acceleration(self):
        self.aircraft.ax = 0
        self.aircraft.ay = 0
        
        if K_a in self.keys_pressed:
            self.aircraft.ax = -acceleration_pressed
        if K_d in self.keys_pressed:
            self.aircraft.ax = acceleration_pressed
        if K_w in self.keys_pressed:
            self.aircraft.ay = acceleration_pressed
        if K_s in self.keys_pressed:
            self.aircraft.ay = -acceleration_pressed
            
    def update(self, dt):
        if not self.running or self.paused or self.game_over:
            return
            
        self.update_acceleration()
        self.aircraft.calc_move(dt)
        self.missile.calc_move(dt)
        
        # Сохраняем траекторию
        self.trajectory.append((
            (self.aircraft.x, self.aircraft.y),
            (self.missile.x, self.missile.y)
        ))
        if len(self.trajectory) > 10000:
            self.trajectory.pop(0)
            
        # Проверка коллизий
        distance = hypot(
            self.missile.x - self.aircraft.x,
            self.missile.y - self.aircraft.y
        )
        if distance < 0.2:
            self.game_over = True
            
        # Проверка победы
        if hypot(self.aircraft.x, self.aircraft.y) < 1.0:
            self.win = True
            self.game_over = True
    
    def draw_direction_arrow(self, surface, color, target_pos, arrow_length=20, arrow_head_size=5, line_width=2):
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
                    end_x - arrow_head_size * math.cos(angle - math.pi/6),
                    end_y - arrow_head_size * math.sin(angle - math.pi/6)
                ),
                (
                    end_x - arrow_head_size * math.cos(angle + math.pi/6),
                    end_y - arrow_head_size * math.sin(angle + math.pi/6)
                )
            ]
            pygame.draw.polygon(surface, color, arrow_points)
            
    def draw(self):
        screen.fill(BLACK)
        self.calculate_viewport()
        
        # Отрисовка зоны победы
        center = self.world_to_screen((0, 0))
        radius = int(1 * self.scale)
        pygame.draw.circle(screen, GREEN, center, radius, 2)
        
        # Отрисовка сетки
        grid_size = 5  # Размер ячейки сетки в мировых координатах
        margin = 2     # Дополнительный запас за пределами видимой области
        
        # Получаем границы видимой области в мировых координатах
        screen_left = (-self.offset_x) / self.scale
        screen_right = (WIDTH - self.offset_x) / self.scale
        screen_top = (HEIGHT - self.offset_y) / self.scale
        screen_bottom = (-self.offset_y) / self.scale

        # Рассчитываем начальные и конечные точки для сетки
        start_x = int(screen_left // grid_size) * grid_size - margin
        end_x = int(screen_right // grid_size) * grid_size + margin
        start_y = int(screen_bottom // grid_size) * grid_size - margin
        end_y = int(screen_top // grid_size) * grid_size + margin

        # Вертикальные линии
        for x in range(start_x, end_x + grid_size, grid_size):
            start = self.world_to_screen((x, start_y))
            end = self.world_to_screen((x, end_y))
            pygame.draw.line(screen, (40, 40, 40), start, end, 1)

        # Горизонтальные линии
        for y in range(start_y, end_y + grid_size, grid_size):
            start = self.world_to_screen((start_x, y))
            end = self.world_to_screen((end_x, y))
            pygame.draw.line(screen, (40, 40, 40), start, end, 1)
            
        # Отрисовка траекторий
        for a_pos, m_pos in self.trajectory:
            a_screen = self.world_to_screen(a_pos)
            m_screen = self.world_to_screen(m_pos)
            pygame.draw.circle(screen, BLUE, a_screen, 1)
            pygame.draw.circle(screen, RED, m_screen, 1)
        
        #self.draw_direction_arrow(screen, GREEN, self.world_to_screen((0, 0))) #Стрелка к нулю
        #self.draw_direction_arrow(screen, RED, self.world_to_screen((self.missile.x, self.missile.y))) #Стрелка к ракете
            
        # Отрисовка объектов
        a_pos = self.world_to_screen((self.aircraft.x, self.aircraft.y))
        m_pos = self.world_to_screen((self.missile.x, self.missile.y))
        pygame.draw.circle(screen, BLUE, a_pos, 8)
        pygame.draw.circle(screen, RED, m_pos, 6)
        
        # Отрисовка текста
        texts = [
            f"Закон наведения: {self.current_law.__name__}",
            "[1-5] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[WASD] - управление самолетом"
        ]
        y = 10
        for text in texts:
            surf = font.render(text, True, WHITE)
            screen.blit(surf, (10, y))
            y += 30
            
        if self.game_over:
            text = "Цель поражена!" if not self.win else "Победа!"
            color = RED if not self.win else GREEN
            surf = font.render(text, True, color)
            screen.blit(surf, (WIDTH//2 - 80, HEIGHT//2))
            
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