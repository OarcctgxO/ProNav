import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from const import *

class Renderer:
    def __init__(self, width, height, land_image, scale):
        self.width = width
        self.height = height
        self.scale = scale
        
        # Инициализация OpenGL
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Загрузка текстуры земли
        self.land_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.land_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        texture_data = pygame.image.tostring(land_image, "RGBA", 1)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            land_image.get_width(),
            land_image.get_height(),
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )

        # Текстура для интерфейса
        self.interface_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )

        # Поверхность для элементов интерфейса
        self.pygame_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.font = pygame.font.SysFont("Impact", 20)

    def world_to_screen(self, pos, airplane_pos, airplane_vel):
        dx = pos[0] - airplane_pos[0]
        dy = pos[1] - airplane_pos[1]
        vx, vy = airplane_vel[0], airplane_vel[1]
        speed = math.hypot(vx, vy)

        if speed < 1e-6:  # eps
            dx_rot = dx
            dy_rot = dy
        else:
            beta = math.atan2(vy, vx)
            alpha = math.pi / 2 - beta
            dx_rot = dx * math.cos(alpha) - dy * math.sin(alpha)
            dy_rot = dx * math.sin(alpha) + dy * math.cos(alpha)

        sx = dx_rot * self.scale
        sy = dy_rot * self.scale
        return (self.width // 2 + int(sx), (self.height // 2 - int(sy)))

    def draw_land(self, airplane_pos, airplane_vel):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        vx, vy = airplane_vel[0], airplane_vel[1]
        speed = math.hypot(vx, vy)
        angle_deg = -math.degrees(math.atan2(vy, vx)) + 90 if speed > 1e-6 else 0

        glPushMatrix()
        glTranslatef(self.width // 2, self.height // 2, 0)
        glRotatef(angle_deg, 0, 0, 1)
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-airplane_pos[0], -airplane_pos[1], 0)

        glBindTexture(GL_TEXTURE_2D, self.land_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(-1000, -1000)
        glTexCoord2f(1, 1)
        glVertex2f(1000, -1000)
        glTexCoord2f(1, 0)
        glVertex2f(1000, 1000)
        glTexCoord2f(0, 0)
        glVertex2f(-1000, 1000)
        glEnd()
        glPopMatrix()

    def draw_direction_arrow(self, surface, color, target_pos, arrow_length=20, arrow_head_size=5, line_width=2):
        center_x, center_y = self.width // 2, self.height // 2
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

    def draw_pygame_elements(self, data):
        self.pygame_surface.fill((0, 0, 0, 0))
        
        # Распаковываем данные для отрисовки
        airplane_pos = data["airplane_pos"]
        airplane_vel = data["airplane_vel"]
        missile_pos = data["missile_pos"]
        trajectory = data["trajectory"]
        current_law_name = data["current_law_name"]
        distances = data["distances"]
        current_fps = data["current_fps"]
        game_over = data["game_over"]
        win = data["win"]

        # Отрисовка зоны победы
        center = self.world_to_screen((0, 0), airplane_pos, airplane_vel)
        pygame.draw.circle(self.pygame_surface, (0, 255, 0), center, int(win_zone_r * self.scale), 2)
        
        center = self.world_to_screen(airplane_pos, airplane_pos, airplane_vel)
        pygame.draw.circle(self.pygame_surface, (0, 0, 0), center, int(plane_size * self.scale), 1)

        # Отрисовка траекторий
        if len(trajectory) > 1:
            air_points = [self.world_to_screen(a_pos, airplane_pos, airplane_vel) for a_pos, _ in trajectory]
            pygame.draw.lines(self.pygame_surface, (0, 0, 0), False, air_points, 1)
            miss_points = [self.world_to_screen(m_pos, airplane_pos, airplane_vel) for _, m_pos in trajectory]
            pygame.draw.lines(self.pygame_surface, (255, 0, 0), False, miss_points, 1)

        a_pos = self.world_to_screen(airplane_pos, airplane_pos, airplane_vel)
        m_pos = self.world_to_screen(missile_pos, airplane_pos, airplane_vel)

        # Отрисовка стрелок направления
        self.draw_direction_arrow(
            self.pygame_surface, (0, 255, 0), self.world_to_screen((0, 0), airplane_pos, airplane_vel)
        )
        self.draw_direction_arrow(self.pygame_surface, (255, 0, 0), m_pos)

        pygame.draw.circle(self.pygame_surface, (0, 0, 0), a_pos, 5)
        pygame.draw.circle(self.pygame_surface, (255, 0, 0), m_pos, 5)

        # Отрисовка текста (левая часть - управление)
        control_texts = [
            f"Закон наведения: {current_law_name}",
            "[1-6] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[AD] - управление самолетом",
        ]
        for i, text in enumerate(control_texts):
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.pygame_surface.blit(text_surface, (10, 10 + i * 25))

        # Отрисовка текста (правая часть - расстояния)
        for i, text in enumerate(distances):
            color = (0, 255, 0) if i == 0 else (255, 0, 0)
            text_surface = self.font.render(text, True, color)
            self.pygame_surface.blit(
                text_surface, (self.width - text_surface.get_width() - 10, 10 + i * 25)
            )

        # FPS
        fps_text = f"FPS: {current_fps:.0f}"
        fps_surface = self.font.render(fps_text, True, (255, 255, 255))
        self.pygame_surface.blit(
            fps_surface, 
            (10, self.height - fps_surface.get_height() - 10)
        )

        if game_over:
            text = "Цель поражена!" if not win else "Победа!"
            color = (255, 0, 0) if not win else (0, 255, 0)
            surf = self.font.render(text, True, color)
            self.pygame_surface.blit(
                surf, (self.width // 2 - surf.get_width() // 2, self.height // 2)
            )

        # Обновляем текстуру интерфейса
        texture_data = pygame.image.tostring(self.pygame_surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            self.width,
            self.height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )

    def draw(self, data):
        self.draw_land(data["airplane_pos"], data["airplane_vel"])
        self.draw_pygame_elements(data)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(0, 0)
        glTexCoord2f(1, 1)
        glVertex2f(self.width, 0)
        glTexCoord2f(1, 0)
        glVertex2f(self.width, self.height)
        glTexCoord2f(0, 0)
        glVertex2f(0, self.height)
        glEnd()

        pygame.display.flip()

    def set_scale(self, scale):
        self.scale = scale