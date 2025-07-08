import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import warnings

warnings.filterwarnings(
    "ignore", category=UserWarning, message="pkg_resources is deprecated"
)
import arcade
import numpy as np
import math
import const, simulation
import sys, os

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


def load_image(file_name: str):
    """Загружает изображение file_name из директории скрипта или EXE."""
    try:
        if getattr(sys, "frozen", False):
            # Для собранного EXE
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            # Для режима разработки
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
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)
        self.sim_scale = 20
        self.camera = arcade.Camera2D(
            viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            zoom=self.sim_scale,
        )
        self.keys_pressed = set()
        self.sim = simulation.Simulation()
        self.toggle_keys = (
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
        self.push_keys = (arcade.key.A, arcade.key.D)

    def setup(self):
        self.land_sprite = arcade.SpriteList()
        self.land_sprite.append(arcade.Sprite(load_image("land.png"), 1, center_x=0, center_y=0, angle=0))
        
        self.airplane_sprite = arcade.SpriteList()
        self.airplane_sprite.append(arcade.Sprite(load_image("aircraft.png"), 0.01, center_x=0, center_y=0, angle=0))
        
        self.missile_sprite = arcade.SpriteList()
        self.missile_sprite.append(arcade.Sprite(load_image("missile.png"), 0.001, center_x=0, center_y=0, angle=0))

        self.camera = arcade.Camera2D(
            viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
            position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
            zoom=1.0,
        )

    def update_camera(self):
        self.camera.zoom = self.sim_scale
        self.camera.position = (self.sim.airplane.x, self.sim.airplane.y)
        up_vector = (self.sim.airplane.vx, self.sim.airplane.vy)
        self.camera.up = up_vector

    def toggle(self, key, modifiers):
        if key in self.toggle_keys[:6]:
            number = self.toggle_keys.index(key) + 1
            self.sim.current_law = self.sim.laws[number]
            self.sim.reset()
            self.sim.running = False
        elif key is arcade.key.SPACE:   #если читаешь это - спроси почему я решил, что можно сравнивать через is
            self.sim.running = not self.sim.running
        elif key is arcade.key.R:
            self.sim.reset()
            self.sim.running = False
        elif key is arcade.key.ESCAPE:
            self.close()

    def on_key_press(self, key, modifiers):
        """Обработка нажатия клавиш"""
        if key in self.push_keys:
            self.keys_pressed.add(key)
        elif key in self.toggle_keys:
            self.toggle(key, modifiers)

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
        dt = 1 / const.FPS
        self.clear()
        self.sim.handle_input(self.keys_pressed)
        self.sim.update(dt)
        self.update_camera()
        self.camera.use()
        self.land_sprite.draw()
        
        arcade.draw_lines(self.sim.trajectory_aircraft, arcade.color.WHITE_SMOKE)
        
        self.airplane_sprite[0].center_x = self.sim.airplane.x
        self.airplane_sprite[0].center_y = self.sim.airplane.y
        self.airplane_sprite[0].angle = 90 - math.degrees(math.atan2(self.sim.airplane.vy, self.sim.airplane.vx))
        self.airplane_sprite.draw()
        
        self.missile_sprite[0].center_x = self.sim.missile.x
        self.missile_sprite[0].center_y = self.sim.missile.y
        self.missile_sprite[0].angle = 90 - math.degrees(math.atan2(self.sim.missile.vy, self.sim.missile.vx))
        self.missile_sprite.draw()
        
        arcade.draw_circle_filled(self.sim.airplane.x, self.sim.airplane.y, 1 / self.sim_scale, arcade.color.BLUE, num_segments=64)
        arcade.draw_circle_filled(self.sim.missile.x, self.sim.missile.y, 1 / self.sim_scale, arcade.color.RED, num_segments=64)
        self.camera.unproject((0, 0))


if __name__ == "__main__":
    window = ArcadeRenderer()
    window.setup()
    arcade.run()
