import arcade
import numpy as np
import const
import sys, os

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
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Test window")
        arcade.set_background_color(arcade.color.BLACK)
        self.sim_scale = const.scale
        self.land_sprite = None
    
    def setup_land(self):
        self.land_sprite = arcade.Sprite(load_image('land.png'), scale = self.sim_scale)
        
        self.land_sprite.center_x = SCREEN_WIDTH // 2
        self.land_sprite.center_y = SCREEN_HEIGHT // 2
    
    def on_draw(self):
        arcade.start_render()
        self.land_sprite.draw()
        
if __name__ == "__main__":
    window = ArcadeRenderer()
    window.setup_land()
    arcade.run()