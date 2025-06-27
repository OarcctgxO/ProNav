import pygame
from OpenGL.GL import *  # type: ignore
from OpenGL.GLU import *  # type: ignore
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
        texture_data = pygame.image.tostring(land_image, "RGBA", 1)  # type: ignore
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

    def draw_land(self, airplane_pos, airplane_vel):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore
        glLoadIdentity()

        vx, vy = airplane_vel
        speed = math.hypot(vx, vy)
        angle_deg = -math.degrees(math.atan2(vy, vx)) + 90 if speed > 1e-6 else 0

        glPushMatrix()
        glTranslatef(self.width / 2, self.height / 2, 0)
        glRotatef(angle_deg, 0, 0, 1)
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-airplane_pos[0], -airplane_pos[1], 0)

        glBindTexture(GL_TEXTURE_2D, self.land_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(-1000, -1000)
        glTexCoord2f(1, 1); glVertex2f(1000, -1000)
        glTexCoord2f(1, 0); glVertex2f(1000, 1000)
        glTexCoord2f(0, 0); glVertex2f(-1000, 1000)
        glEnd()
        glPopMatrix()

    def draw_direction_arrow(self, surface, color, target_pos, arrow_length=20, arrow_head_size=5, line_width=2):
        cx, cy = self.width / 2, self.height / 2
        tx, ty = target_pos
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        if dist <= 0:
            return

        nx, ny = dx / dist, dy / dist
        ex, ey = cx + nx * arrow_length, cy + ny * arrow_length

        pygame.draw.line(surface, color, (cx, cy), (ex, ey), line_width)
        ang = math.atan2(dy, dx)
        pts = [
            (ex, ey),
            (ex - arrow_head_size * math.cos(ang - math.pi / 6),
             ey - arrow_head_size * math.sin(ang - math.pi / 6)),
            (ex - arrow_head_size * math.cos(ang + math.pi / 6),
             ey - arrow_head_size * math.sin(ang + math.pi / 6)),
        ]
        pygame.draw.polygon(surface, color, pts)

    def draw_pygame_elements(self, data):
        self.pygame_surface.fill((0, 0, 0, 0))

        ap = data["airplane_pos"]
        av = data["airplane_vel"]
        mp = data["missile_pos"]
        traj = data["trajectory"]
        law = data["current_law_name"]
        dists = data["distances"]
        fps = data["current_fps"]
        game_over = data["game_over"]
        win = data["win"]

        # Вычисляем параметры поворота один раз
        vx, vy = av
        speed = math.hypot(vx, vy)
        if speed > 1e-6:
            beta = math.atan2(vy, vx)
            alpha = math.pi / 2 - beta
            c, s = math.cos(alpha), math.sin(alpha)
        else:
            c, s = 1.0, 0.0

        # Функция для преобразования точки мира в экран
        def w2s(pos):
            dx = pos[0] - ap[0]
            dy = pos[1] - ap[1]
            dxr = dx * c - dy * s
            dyr = dx * s + dy * c
            sx = int(dxr * self.scale)
            sy = int(dyr * self.scale)
            return (int(self.width / 2 + sx), int(self.height / 2 - sy))

        # Зона победы
        center0 = w2s((0, 0))
        pygame.draw.circle(self.pygame_surface, (0, 255, 0), center0, int(win_zone_r * self.scale), 2)
        # Самолет
        center1 = w2s(ap)
        pygame.draw.circle(self.pygame_surface, (0, 0, 0), center1, int(plane_size * self.scale), 1)

        # Траектории
        if len(traj) > 1:
            air_pts = [w2s(a_p) for a_p, _ in traj]
            miss_pts = [w2s(m_p) for _, m_p in traj]
            pygame.draw.lines(self.pygame_surface, (0, 0, 0), False, air_pts, 1)
            pygame.draw.lines(self.pygame_surface, (255, 0, 0), False, miss_pts, 1)

        # Направляющие стрелки
        m_screen = w2s(mp)
        self.draw_direction_arrow(self.pygame_surface, (0, 255, 0), w2s((0, 0)))
        self.draw_direction_arrow(self.pygame_surface, (255, 0, 0), m_screen)

        # Маркеры
        pygame.draw.circle(self.pygame_surface, (0, 0, 0), w2s(ap), 5)
        pygame.draw.circle(self.pygame_surface, (255, 0, 0), m_screen, 5)

        # Текстовая часть (лево)
        ctrl = [
            f"Закон наведения: {law}",
            "[1-6] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[AD] - управление самолетом",
            "[Esc] - выход"
        ]
        for i, txt in enumerate(ctrl):
            surf = self.font.render(txt, True, (255, 255, 255))
            self.pygame_surface.blit(surf, (10, 10 + i * 25))

        # Текст (расстояния, право)
        for i, txt in enumerate(dists):
            col = (0, 255, 0) if i == 0 else (255, 0, 0)
            surf = self.font.render(txt, True, col)
            x = self.width - surf.get_width() - 10
            self.pygame_surface.blit(surf, (x, 10 + i * 25))

        # FPS
        fps_s = self.font.render(f"FPS: {fps:.0f}", True, (255, 255, 255))
        self.pygame_surface.blit(fps_s, (10, self.height - fps_s.get_height() - 10))

        # Game Over
        if game_over:
            msg = "Победа!" if win else "Цель поражена!"
            clr = (0, 255, 0) if win else (255, 0, 0)
            go_s = self.font.render(msg, True, clr)
            x = self.width / 2 - go_s.get_width() / 2
            y = self.height / 2
            self.pygame_surface.blit(go_s, (x, y))

        # Обновляем текстуру интерфейса
        tex_data = pygame.image.tostring(self.pygame_surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glTexSubImage2D(
            GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
            GL_RGBA, GL_UNSIGNED_BYTE, tex_data
        )

    def draw(self, data):
        self.draw_land(data["airplane_pos"], data["airplane_vel"])
        self.draw_pygame_elements(data)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.interface_texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(self.width, 0)
        glTexCoord2f(1, 0); glVertex2f(self.width, self.height)
        glTexCoord2f(0, 0); glVertex2f(0, self.height)
        glEnd()

        pygame.display.flip()

    def set_scale(self, scale):
        self.scale = scale