import arcade
import numpy as np
import math
import const, simulation
import sys, os

from main import airplane

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

def load_image(file_name: str):
    """Загружает изображение file_name из директории скрипта или EXE."""
    try:
        if getattr(sys, 'frozen', False):
            # Для собранного EXE
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # Для режима разработки
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        image_path = os.path.join(base_path, file_name)
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл '{file_name}' не найден по пути: {image_path}")
        
        return image_path
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки изображения: {str(e)}")
    
class ArcadeRenderer(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)
        self.sim_scale = 1
        self.camera = arcade.Camera2D(viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                                      position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                                      zoom=1.0
                                      )
        self.keys_pressed = set()
        self.sim = simulation.Simulation()
        
    def setup(self):
        self.land_sprite = arcade.SpriteList()
        self.land_sprite.append(arcade.Sprite(load_image('land.png'), 1))
        self.land_sprite[0].center_x = SCREEN_WIDTH // 2
        self.land_sprite[0].center_y = SCREEN_HEIGHT // 2
        
        self.camera = arcade.Camera2D(viewport=arcade.types.Viewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                                      position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                                      zoom=1.0)
        
    def update_camera(self):
        self.camera.zoom = 1.0 / self.sim_scale
        self.camera.position = (self.xp, self.yp)
        up_vector = (self.vxp, self.vyp)
        self.camera.up = up_vector
    
    def update_render_data(self, render_data: dict):
        self.xp, self.yp = render_data['airplane_pos']
        self.vxp, self.vyp = render_data['airplane_vel']
        self.xt, self.yt = render_data['missile_pos']
        self.vxt, self.vyt = render_data['missile_vel']
        self.trajectory = render_data['trajectory']
        self.current_law_name = render_data['current_law_name']
        self.win_distance = render_data['distances'][0]
        self.mis_distance = render_data['distances'][1]
        self.fps = render_data['current_fps']
        self.game_over = render_data['game_over']
        self.win = render_data['win']
        self.sim_scale = render_data['scale']
        
        self.update_camera()
        
    def on_key_press(self, key, modifiers):
        """Обработка нажатия клавиш"""
        tracked_keys = {
            arcade.key.KEY_1, arcade.key.KEY_2, arcade.key.KEY_3,
            arcade.key.KEY_4, arcade.key.KEY_5, arcade.key.KEY_6,
            arcade.key.A, arcade.key.D, arcade.key.ESCAPE, arcade.key.SPACE, arcade.key.R
        }
        if key in tracked_keys:
            self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        """Обработка отпускания клавиш"""
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Обработка колесика мыши (scroll_y: вверх > 0, вниз < 0)"""
        if scroll_y > 0:
            self.keys_pressed.add("MOUSE_UP")
        elif scroll_y < 0:
            self.keys_pressed.add("MOUSE_DOWN")
        
    def get_keys(self):
        keys = self.keys_pressed.copy()
        
        if "MOUSE_UP" in keys:
            self.keys_pressed.discard("MOUSE_UP")
        if "MOUSE_DOWN" in keys:
            self.keys_pressed.discard("MOUSE_DOWN")
        
        return keys
        
    def on_draw(self):
        self.clear()
        self.camera.use()
        self.land_sprite.draw()
        
if __name__ == "__main__":
    window = ArcadeRenderer()
    window.setup()
    arcade.run()