import arcade
import numpy as np
import math
import const
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
        self.camera = arcade.Camera2D(viewport=arcade.View(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                                      position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                                      zoom=1.0)
        
    def setup(self):
        self.land_sprite = arcade.SpriteList()
        self.land_sprite.append(arcade.Sprite(load_image('land.png'), 1))
        self.land_sprite[0].center_x = SCREEN_WIDTH // 2
        self.land_sprite[0].center_y = SCREEN_HEIGHT // 2
        
    def update_camera(self):
        self.camera.zoom = 1.0 / self.sim_scale
        self.camera.position = (self.xp, self.yp)
        angle_rad = math.atan2(self.vxp, self.vyp)
        self.camera.angle = math.degrees(angle_rad)
    
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
        
    def w2s(self, x, y):
        pass
        
    def on_draw(self):
        self.clear()
        self.camera.use()
        self.land_sprite.draw()
        
if __name__ == "__main__":
    window = ArcadeRenderer()
    window.setup()
    arcade.run()