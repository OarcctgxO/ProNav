import pygame
from OpenGL.GL import *  # type: ignore
from OpenGL.GLU import *  # type: ignore
from OpenGL.GLUT import *  # type: ignore
import math
import freetype
from const import *


def flip_y(y, height):
    return height - y


class Renderer:
    def __init__(self, width, height, land_image, scale):
        self.width = width
        self.height = height
        self.scale = scale
        self.glyph_cache = {}  # Кеш для глифов

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
        try:
            self.face = freetype.Face("C:\\Windows\\Fonts\\impact.ttf")
            self.face.set_char_size(24 * 64)
        except:
            self.face = None
        self.interface_pixels = (GLubyte * (width * height * 4))()

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

    def draw_direction_arrow(
        self,
        surface,
        color,
        target_pos,
        arrow_length=20,
        arrow_head_size=5,
        line_width=2,
    ):
        cx, cy = self.width / 2, self.height / 2
        tx, ty = target_pos
        dx, dy = tx - cx, ty - cy
        dist = math.hypot(dx, dy)
        if dist <= 0:
            return

        nx, ny = dx / dist, dy / dist
        ex, ey = cx + nx * arrow_length, cy + ny * arrow_length

        self.draw_line((cx, cy), (ex, ey), color, line_width)
        ang = math.atan2(dy, dx)
        pts = [
            (ex, ey),
            (
                ex - arrow_head_size * math.cos(ang - math.pi / 6),
                ey - arrow_head_size * math.sin(ang - math.pi / 6),
            ),
            (
                ex - arrow_head_size * math.cos(ang + math.pi / 6),
                ey - arrow_head_size * math.sin(ang + math.pi / 6),
            ),
        ]
        self.draw_polygon(pts, color)

    def draw_circle(self, center, radius, color, width):
        """Draw a circle using OpenGL"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0 if len(color) > 3 else 1.0,
        )
        glBegin(GL_TRIANGLE_FAN if width <= 1 else GL_LINE_LOOP)
        for i in range(32):
            angle = 2.0 * math.pi * i / 32
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            glVertex2f(x, y)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_line(self, start, end, color, width):
        """Draw a line using OpenGL"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0 if len(color) > 3 else 1.0,
        )
        glLineWidth(width)
        glBegin(GL_LINES)
        glVertex2f(start[0], start[1])
        glVertex2f(end[0], end[1])
        glEnd()
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_lines(self, points, color, width):
        """Draw connected lines using OpenGL"""
        if len(points) < 2:
            return
        glDisable(GL_TEXTURE_2D)
        glColor4f(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0 if len(color) > 3 else 1.0,
        )
        glLineWidth(width)
        glBegin(GL_LINE_STRIP)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_polygon(self, points, color):
        """Draw a filled polygon using OpenGL"""
        glDisable(GL_TEXTURE_2D)
        glColor4f(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0 if len(color) > 3 else 1.0,
        )
        glBegin(GL_POLYGON)
        for point in points:
            glVertex2f(point[0], point[1])
        glEnd()
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def render_text(self, text, pos, color):
        if not self.face:
            return
            
        prev_texture_enabled = glIsEnabled(GL_TEXTURE_2D)
        prev_color = (GLfloat * 4)()
        glGetFloatv(GL_CURRENT_COLOR, prev_color)
        
        glColor4f(
            color[0] / 255.0,
            color[1] / 255.0,
            color[2] / 255.0,
            color[3] / 255.0 if len(color) > 3 else 1.0,
        )
        
        x, y = pos
        y = flip_y(y, self.height)
        
        glEnable(GL_TEXTURE_2D)
        
        # Сохраняем текущие настройки выравнивания
        prev_alignment = glGetIntegerv(GL_UNPACK_ALIGNMENT)
        
        for char in text:
            if char not in self.glyph_cache:
                self.face.load_char(char)
                slot = self.face.glyph
                bitmap = slot.bitmap
                w, h = bitmap.width, bitmap.rows
                
                if w == 0 or h == 0:
                    self.glyph_cache[char] = {
                        'texture': None,
                        'width': w,
                        'height': h,
                        'left': slot.bitmap_left,
                        'top': slot.bitmap_top,
                        'advance': slot.advance.x >> 6
                    }
                    continue
                    
                texture_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                
                data = bitmap.buffer
                texture_data = (GLubyte * (2 * w * h))()
                
                # Устанавливаем выравнивание 1 байт
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                
                # Копирование данных с учетом выравнивания
                for j in range(h):
                    row_start = j * w
                    for i in range(w):
                        idx = 2 * (row_start + i)
                        byte = data[row_start + i]
                        texture_data[idx] = 255  # Luminance
                        texture_data[idx + 1] = byte  # Alpha
                
                glTexImage2D(
                    GL_TEXTURE_2D,
                    0,
                    GL_LUMINANCE_ALPHA,
                    w,
                    h,
                    0,
                    GL_LUMINANCE_ALPHA,
                    GL_UNSIGNED_BYTE,
                    texture_data,
                )
                
                self.glyph_cache[char] = {
                    'texture': texture_id,
                    'width': w,
                    'height': h,
                    'left': slot.bitmap_left,
                    'top': slot.bitmap_top,
                    'advance': slot.advance.x >> 6
                }
            
            glyph = self.glyph_cache[char]
            if glyph['texture'] is None:
                x += glyph['advance']
                continue
                
            w = glyph['width']
            h = glyph['height']
            
            glBindTexture(GL_TEXTURE_2D, glyph['texture'])
            glPushMatrix()
            
            # Округление координат для избежания смазывания
            draw_x = round(x + glyph['left'])
            draw_y = round(y - glyph['top'])
            glTranslatef(draw_x, draw_y, 0)
            
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex2f(0, 0)
            glTexCoord2f(1, 1); glVertex2f(w, 0)
            glTexCoord2f(1, 0); glVertex2f(w, h)
            glTexCoord2f(0, 0); glVertex2f(0, h)
            glEnd()
            
            glPopMatrix()
            x += glyph['advance']
        
        # Восстанавливаем предыдущие настройки
        glPixelStorei(GL_UNPACK_ALIGNMENT, prev_alignment)
        
        if prev_texture_enabled:
            glEnable(GL_TEXTURE_2D)
        else:
            glDisable(GL_TEXTURE_2D)
        
        glColor4fv(prev_color)

    def draw_pygame_elements(self, data):
        # Clear and prepare for interface drawing
        glLoadIdentity()

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
            return (
                int(self.width / 2 + sx),
                flip_y(int(self.height / 2 - sy), self.height),
            )

        # Зона победы
        center0 = w2s((0, 0))
        self.draw_circle(center0, int(win_zone_r * self.scale), (0, 255, 0, 255), 2)
        # Самолет
        center1 = w2s(ap)
        self.draw_circle(center1, int(plane_size * self.scale), (0, 0, 0, 255), 1)

        # Траектории
        if len(traj) > 1:
            air_pts = [w2s(a_p) for a_p, _ in traj]
            miss_pts = [w2s(m_p) for _, m_p in traj]
            self.draw_lines(air_pts, (0, 0, 0, 255), 1)
            self.draw_lines(miss_pts, (255, 0, 0, 255), 1)

        # Направляющие стрелки
        m_screen = w2s(mp)
        self.draw_direction_arrow(None, (0, 255, 0), w2s((0, 0)))
        self.draw_direction_arrow(None, (255, 0, 0), m_screen)

        # Маркеры
        self.draw_circle(w2s(ap), 5, (0, 0, 0, 255), 1)
        self.draw_circle(m_screen, 5, (255, 0, 0, 255), 1)

        # Текстовая часть (лево)
        ctrl = [
            f"Закон наведения: {law}",
            "[1-6] - выбор закона",
            "[SPACE] - старт/пауза",
            "[R] - сброс",
            "[AD] - управление самолетом",
            "[Esc] - выход",
        ]
        for i, txt in enumerate(ctrl):
            self.render_text(txt, (10, 10 + i * 25), (255, 255, 255, 255))

        # Текст (расстояния, право)
        for i, txt in enumerate(dists):
            col = (0, 255, 0) if i == 0 else (255, 0, 0)
            self.render_text(txt, (self.width - 300, 10 + i * 25), col)

        # FPS
        fps_text = f"FPS: {fps:.0f}"
        self.render_text(fps_text, (10, self.height - 30), (255, 255, 255, 255))

        # Game Over
        if game_over:
            msg = "Победа!" if win else "Цель поражена!"
            clr = (0, 255, 0) if win else (255, 0, 0)
            self.render_text(msg, (self.width / 2 - 50, self.height / 2), clr)

    def draw(self, data):
        self.draw_land(data["airplane_pos"], data["airplane_vel"])
        self.draw_pygame_elements(data)
        pygame.display.flip()

    def set_scale(self, scale):
        self.scale = scale
