import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from noise import snoise2

# Параметры генерации
width, height = 1000, 1000
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


# Генерация карты высот с возможностью задания сида
def generate_height_map(width, height, scale, octaves, persistence, lacunarity, seed):
    height_map = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            height_map[y][x] = snoise2(
                x / scale,
                y / scale,
                octaves=octaves,
                persistence=persistence,
                lacunarity=lacunarity,
                repeatx=1024,
                repeaty=1024,
                base=seed,
            )  # Используем сид
    return height_map


# Функция для интерполяции цвета
def interpolate_color(color1, color2, factor):
    return [int(color1[i] * (1 - factor) + color2[i] * factor) for i in range(3)]


# Преобразование высот в значения для цветов с плавными переходами
def height_to_color(height_map):
    color_map = np.zeros((height_map.shape[0], height_map.shape[1], 3), dtype=np.uint8)
    for y in range(height_map.shape[0]):
        for x in range(height_map.shape[1]):
            height = height_map[y][x]
            if height < deep_ocean_height:
                color_map[y][x] = [0, 0, 100]  # Глубокий океан
            elif height < ocean_height:
                factor = (height - deep_ocean_height) / (
                    ocean_height - deep_ocean_height
                )
                color_map[y][x] = interpolate_color(
                    [0, 0, 100], [0, 0, 200], factor
                )  # Плавный переход к океану
            elif height < beach_height:
                factor = (height - ocean_height) / (beach_height - ocean_height)
                color_map[y][x] = interpolate_color(
                    [0, 0, 200], [200, 200, 100], factor
                )  # Плавный переход к пляжу
            elif height < plain_height:
                factor = (height - beach_height) / (plain_height - beach_height)
                color_map[y][x] = interpolate_color(
                    [200, 200, 100], [100, 200, 100], factor
                )  # Плавный переход к равнине
            elif height < forest_height:
                factor = (height - plain_height) / (forest_height - plain_height)
                color_map[y][x] = interpolate_color(
                    [100, 200, 100], [34, 139, 34], factor
                )  # Плавный переход к лесу
            elif height < mountain_height:
                factor = (height - forest_height) / (mountain_height - forest_height)
                color_map[y][x] = interpolate_color(
                    [34, 139, 34], [60, 60, 60], factor
                )  # Плавный переход к горам
            else:
                factor = (height - mountain_height) / (1.0 - mountain_height)
                color_map[y][x] = interpolate_color(
                    [60, 60, 60], [240, 240, 240], factor
                )  # Плавный переход к заснеженным горам
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
