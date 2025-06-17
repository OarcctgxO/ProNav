import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from noise import snoise2

# Параметры генерации
width, height = 2000, 2000
scale = 300.0  # Масштаб для больших материков и морей
seed = 6  # Сид генерации

# Параметры высот для биомов
deep_ocean_height = -0.2
ocean_height = -0.1
beach_height = 0.0
plain_height = 0.15
forest_height = 0.3
mountain_height = 0.4

octaves = 6  # Количество октав
persistence = 0.5
lacunarity = 2.0

# Генерация карты высот с использованием numpy для ускорения
def generate_height_map(width, height, scale, octaves, persistence, lacunarity, seed):
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    
    # Векторизованный расчет шума
    height_map = np.vectorize(snoise2)(
        xx / scale,
        yy / scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=lacunarity,
        repeatx=1024,
        repeaty=1024,
        base=seed
    )
    return height_map

# Преобразование высот в цвета с более резкими переходами
def height_to_color(height_map):
    color_map = np.zeros((*height_map.shape, 3), dtype=np.uint8)
    
    # Маски для каждого биома
    deep_ocean_mask = height_map < deep_ocean_height
    ocean_mask = (height_map >= deep_ocean_height) & (height_map < ocean_height)
    beach_mask = (height_map >= ocean_height) & (height_map < beach_height)
    plain_mask = (height_map >= beach_height) & (height_map < plain_height)
    forest_mask = (height_map >= plain_height) & (height_map < forest_height)
    mountain_mask = (height_map >= forest_height) & (height_map < mountain_height)
    snow_mountain_mask = height_map >= mountain_height
    
    # Базовые цвета для биомов
    color_map[deep_ocean_mask] = [0, 0, 100]          # Глубокий океан
    color_map[ocean_mask] = [0, 0, 200]               # Океан
    color_map[beach_mask] = [200, 200, 100]           # Пляж
    color_map[plain_mask] = [100, 200, 100]           # Равнина
    color_map[forest_mask] = [34, 139, 34]            # Лес
    color_map[mountain_mask] = [60, 60, 60]           # Горы
    color_map[snow_mountain_mask] = [240, 240, 240]   # Заснеженные горы
    
    # Добавляем небольшие плавные переходы только между соседними биомами
    transition_width = 0.02  # Ширина перехода (меньше значение = резче переход)
    
    # Переход между глубоким океаном и океаном
    transition_mask = (height_map >= deep_ocean_height - transition_width) & (height_map < deep_ocean_height + transition_width)
    factor = (height_map[transition_mask] - (deep_ocean_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([0, 0, 100]) * (1 - factor[..., np.newaxis]) + np.array([0, 0, 200]) * factor[..., np.newaxis]
    
    # Переход между океаном и пляжем
    transition_mask = (height_map >= ocean_height - transition_width) & (height_map < ocean_height + transition_width)
    factor = (height_map[transition_mask] - (ocean_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([0, 0, 200]) * (1 - factor[..., np.newaxis]) + np.array([200, 200, 100]) * factor[..., np.newaxis]
    
    # Переход между пляжем и равниной
    transition_mask = (height_map >= beach_height - transition_width) & (height_map < beach_height + transition_width)
    factor = (height_map[transition_mask] - (beach_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([200, 200, 100]) * (1 - factor[..., np.newaxis]) + np.array([100, 200, 100]) * factor[..., np.newaxis]
    
    # Переход между равниной и лесом
    transition_mask = (height_map >= plain_height - transition_width) & (height_map < plain_height + transition_width)
    factor = (height_map[transition_mask] - (plain_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([100, 200, 100]) * (1 - factor[..., np.newaxis]) + np.array([34, 139, 34]) * factor[..., np.newaxis]
    
    # Переход между лесом и горами
    transition_mask = (height_map >= forest_height - transition_width) & (height_map < forest_height + transition_width)
    factor = (height_map[transition_mask] - (forest_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([34, 139, 34]) * (1 - factor[..., np.newaxis]) + np.array([60, 60, 60]) * factor[..., np.newaxis]
    
    # Переход между горами и заснеженными горами
    transition_mask = (height_map >= mountain_height - transition_width) & (height_map < mountain_height + transition_width)
    factor = (height_map[transition_mask] - (mountain_height - transition_width)) / (2 * transition_width)
    color_map[transition_mask] = np.array([60, 60, 60]) * (1 - factor[..., np.newaxis]) + np.array([240, 240, 240]) * factor[..., np.newaxis]
    
    return color_map

# Генерация высот и цветов
height_map = generate_height_map(
    width, height, scale, octaves, persistence, lacunarity, seed
)
color_map = height_to_color(height_map)

# Сохранение изображения
image = Image.fromarray(color_map)
image.save("land.png")

# Отображение изображения
plt.imshow(color_map)
plt.axis("off")  # Скрыть оси
plt.show()