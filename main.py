import arcade
import ctypes
import numpy as np
import math
import sys, os, time
from numba import njit

import const, simulation

dpi = ctypes.windll.gdi32.GetDeviceCaps(ctypes.windll.gdi32.CreateCompatibleDC(0), 88)
scale_factor = dpi / 96  

SCREEN_WIDTH, SCREEN_HEIGHT = [size // scale_factor for size in arcade.get_display_size()]
@njit
def pixel_norm(FHD_size: float) -> float:
    return FHD_size * SCREEN_HEIGHT / 1080


def load_image(file_name: str):
    """Загружает изображение file_name из директории .py или EXE."""
    try:
        if getattr(sys, "frozen", False):
            # Для собранного EXE
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            # Для .py
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        image_path = os.path.join(base_path, file_name)
        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Файл '{file_name}' не найден по пути: {image_path}"
            )

        return image_path
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки изображения: {str(e)}")


class ArcadeRenderer(arcade.Window):
    """Главный класс, собирает вместе симуляцию и отрисовку"""
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.set_fullscreen(True)
        arcade.set_background_color(arcade.color.BLACK)
        self.sim_scale = const.scale
        self.camera = arcade.Camera2D(
            viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            zoom=self.sim_scale,
        )
        self.keys_pressed = set()
        self.sim = simulation.Simulation()
        self.push_to_toggle_keys = (
            arcade.key.KEY_1,
            arcade.key.KEY_2,
            arcade.key.KEY_3,
            arcade.key.KEY_4,
            arcade.key.KEY_5,
            arcade.key.KEY_6,
            arcade.key.ESCAPE,
            arcade.key.SPACE,
            arcade.key.R,
        )
        self.push_keys = (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D)

        self.land_sprite = arcade.SpriteList()
        self.land_sprite.append(arcade.Sprite(load_image("land.png"), 1, center_x=0, center_y=0, angle=0))

        self.airplane_sprite = arcade.SpriteList()
        self.airplane_sprite.append(arcade.Sprite(load_image("aircraft.png"), 0.01, center_x=0, center_y=0, angle=0))

        self.missile_sprite = arcade.SpriteList()
        self.missile_sprite.append(arcade.Sprite(load_image("missile.png"), 0.004, center_x=0, center_y=0, angle=0))

        self.boom_sprite = arcade.SpriteList()
        self.boom_sprite.append(arcade.Sprite(load_image("BOOM.png"), 0.012, center_x=0, center_y=0, angle=0))
        
        self.camera = arcade.Camera2D(
            viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            zoom=1.0,
        )

    def update_camera(self):
        """Обновить положение камеры с учетом положения самолета"""
        self.camera.zoom = self.sim_scale
        self.camera.position = (self.sim.airplane.x, self.sim.airplane.y)
        up_vector = (self.sim.airplane.vx, self.sim.airplane.vy)
        self.camera.up = up_vector

    def push_to_toggle(self, key, modifiers):
        """Обрабатывает кнопки с коротким нажатием (без длительности)"""        
        if key in self.push_to_toggle_keys[:6]:
            number = self.push_to_toggle_keys.index(key) + 1
            self.sim.current_law = self.sim.laws[number]
            self.sim.reset()
            self.sim.running = False
        elif key == arcade.key.SPACE:
            self.sim.running = not self.sim.running
        elif key == arcade.key.R:
            self.sim.reset()
            self.sim.running = False
        elif key == arcade.key.ESCAPE:
            self.close()
            
    def draw_speed_gauge(self) -> None:
        """Рисует прямоугольник, который закрашен пропорционально текущей скорости"""
        
        r = arcade.LBWH(SCREEN_WIDTH-pixel_norm(25), pixel_norm(5), pixel_norm(20), pixel_norm(100))
        arcade.draw_rect_outline(r, arcade.color.WHITE_SMOKE, pixel_norm(2))
        r = arcade.LBWH(SCREEN_WIDTH-pixel_norm(25), pixel_norm(5), pixel_norm(20), pixel_norm(100) * self.sim.airplane.current_speed / const.airplane_max_speed)
        arcade.draw_rect_filled(r, arcade.color.WHITE_SMOKE)

    def draw_texts(self):
        """Отрисовать текст для HUD"""
        text_size = pixel_norm(20)
        text_top_left = (
            f"[1-6] Закон наведения: {self.sim.current_law.__name__}",
            "[Space] Старт / Пауза",
            "[W, A, S, D] Управление",
            "[R] Сброс"
            "[ESC] Выход",
        )
        text_dist_win = f"Расстояние до зоны победы: {math.floor(math.hypot(self.sim.airplane.x, self.sim.airplane.y))}"
        text_dist_missile = f"Расстояние до ракеты: {math.floor(math.hypot(self.sim.airplane.x - self.sim.missile.x, self.sim.airplane.y - self.sim.missile.y))}"
        text_FPS = f'FPS: {math.floor(self.sim.current_fps)}'
        text_bot_right = "Скорость самолета"

        text_top_left = arcade.Text(
            '\n'.join(text_top_left),
            pixel_norm(5), SCREEN_HEIGHT - pixel_norm(5),
            arcade.color.WHITE,
            text_size,
            align='left',
            width=int(pixel_norm(500)),
            multiline=True,
            anchor_x='left', anchor_y='top',
            font_name="impact"
        )

        text_dist_win = arcade.Text(
            text_dist_win,
            SCREEN_WIDTH - pixel_norm(390),
            SCREEN_HEIGHT - pixel_norm(5),
            arcade.color.GREEN,
            text_size,
            align="left",
            anchor_x="left",
            anchor_y="top",
            font_name="impact"
        )

        text_dist_missile = arcade.Text(
            text_dist_missile,
            SCREEN_WIDTH - pixel_norm(320),
            SCREEN_HEIGHT - pixel_norm(30),
            arcade.color.RED,
            text_size,
            align="left",
            anchor_x="left",
            anchor_y="top",
            font_name="impact"
        )

        text_FPS = arcade.Text(
            text_FPS,
            pixel_norm(5),
            pixel_norm(5),
            arcade.color.WHITE,
            text_size,
            anchor_x="left",
            anchor_y="bottom",
            font_name="impact"
        )
        
        text_game_over = arcade.Text(
            "Победа!",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + pixel_norm(50),
            arcade.color.GREEN,
            text_size + pixel_norm(1),
            anchor_x="left",
            anchor_y="bottom",
            font_name="impact"
        )
        
        text_bot_right = arcade.Text(
            text_bot_right,
            SCREEN_WIDTH-pixel_norm(30),
            pixel_norm(5),
            arcade.color.WHITE,
            text_size-2,
            anchor_x="right",
            anchor_y="bottom",
            font_name="impact"
        )
        if not self.sim.win:
            text_game_over.text = "Цель перехвачена!"
            text_game_over.color = arcade.color.RED

        texts_hud = (text_top_left, text_dist_win, text_dist_missile, text_FPS, text_bot_right)
        for t in texts_hud:
            t.draw()
        if self.sim.game_over:
            text_game_over.draw()

    def on_key_press(self, key, modifiers):
        """Обработка нажатия клавиш"""
        if key in self.push_keys:
            self.keys_pressed.add(key)
        elif key in self.push_to_toggle_keys:
            self.push_to_toggle(key, modifiers)

    def on_key_release(self, key, modifiers):
        """Обработка отпускания клавиш"""
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Обработка колесика мыши (scroll_y: вверх > 0, вниз < 0)"""
        if scroll_y > 0:
            self.sim_scale = np.clip(self.sim_scale * 1.1, 1, 100)
        elif scroll_y < 0:
            self.sim_scale = np.clip(self.sim_scale * 0.9, 1, 100)

    def on_draw(self):
        """Главный цикл отрисовки."""        
        dt = 1 / self.sim.current_fps
        frame_time_start = time.perf_counter()
        self.clear()
        self.sim.handle_input(self.keys_pressed)
        self.sim.update(dt)
        self.update_camera()

        with self.camera.activate():
            self.land_sprite.draw()

            arcade.draw_circle_outline(0, 0, 5, arcade.color.GREEN, 1 / self.sim_scale, num_segments=64)

            arcade.draw_line_strip(self.sim.trajectory_missile, arcade.color.ORANGE_RED)
            arcade.draw_line_strip(self.sim.trajectory_aircraft, arcade.color.WHITE_SMOKE)

            self.airplane_sprite[0].center_x = self.sim.airplane.x
            self.airplane_sprite[0].center_y = self.sim.airplane.y
            self.airplane_sprite[0].angle = 90 - math.degrees(math.atan2(self.sim.airplane.vy, self.sim.airplane.vx))
            self.airplane_sprite.draw()
            
            self.current_missile_sprite = self.missile_sprite
            if self.sim.game_over and not self.sim.win:
                self.current_missile_sprite = self.boom_sprite
            else:
                self.current_missile_sprite = self.missile_sprite
            self.current_missile_sprite[0].center_x = self.sim.missile.x
            self.current_missile_sprite[0].center_y = self.sim.missile.y
            self.current_missile_sprite[0].angle = 90 - math.degrees(math.atan2 (self.sim.missile.vy, self.sim.missile.vx))
            self.current_missile_sprite.draw()

        self.draw_texts()
        self.draw_speed_gauge()
        
        frame_time = time.perf_counter() - frame_time_start
        min_frame_time = 1 / const.FPS
        diff = min_frame_time - frame_time
        if diff >= 0:
            time.sleep(diff)
        real_FPS = np.clip(1 / frame_time, 1, const.FPS)
        self.sim.current_fps = real_FPS
        
def main():
    window = ArcadeRenderer()
    arcade.run()
    
if __name__ == "__main__":
    main()
