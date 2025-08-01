import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from noise import snoise2

# Параметры генерации
width, height = 4000, 4000
scale = 300.0
seed = 6

# Параметры высот для биомов
deep_ocean_height = -0.2
ocean_height = -0.1
beach_height = 0.0
plain_height = 0.15
forest_height = 0.3
mountain_height = 0.4

# Цвета биомов
deep_ocean_color = [0, 0, 50]
ocean_color = [0, 0, 100]
beach_color = [100, 100, 50]
plain_color = [50, 100, 50]
forest_color = [17, 70, 17]
mountain_color = [30, 30, 30]
snow_mountain_color = [120, 120, 120]

octaves = 6
persistence = 0.5
lacunarity = 2.0

# Дополнительный шум для цветовой вариативности
color_noise_scale = 50.0
color_noise_intensity = 0.20

def generate_height_map(width, height, scale, octaves, persistence, lacunarity, seed):
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    
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

def generate_color_variation(width, height, scale, intensity, seed):
    x = np.arange(width)
    y = np.arange(height)
    xx, yy = np.meshgrid(x, y)
    
    noise = np.vectorize(snoise2)(
        xx / scale,
        yy / scale,
        octaves=1,
        persistence=0.5,
        lacunarity=2.0,
        repeatx=1024,
        repeaty=1024,
        base=seed + 1  # Другой seed для цветового шума
    )
    return noise * intensity

def height_to_color(height_map, color_variation):
    color_map = np.zeros((*height_map.shape, 3), dtype=np.uint8)
    
    # Маски для каждого биома
    deep_ocean_mask = height_map < deep_ocean_height
    ocean_mask = (height_map >= deep_ocean_height) & (height_map < ocean_height)
    beach_mask = (height_map >= ocean_height) & (height_map < beach_height)
    plain_mask = (height_map >= beach_height) & (height_map < plain_height)
    forest_mask = (height_map >= plain_height) & (height_map < forest_height)
    mountain_mask = (height_map >= forest_height) & (height_map < mountain_height)
    snow_mountain_mask = height_map >= mountain_height
    
    # Базовые цвета для биомов с вариациями
    def apply_variation(base_color, mask, variation):
        color = np.array(base_color, dtype=np.float32)
        # Применяем вариацию (темнее-светлее)
        variation_factor = 1.0 + variation[mask] * 0.5  # От 0.85 до 1.15
        varied_color = color * variation_factor[..., np.newaxis]
        # Ограничиваем значения 0-255
        return np.clip(varied_color, 0, 255).astype(np.uint8)
    
    # Применяем цветовые вариации к каждому биому
    color_map[deep_ocean_mask] = apply_variation(deep_ocean_color, deep_ocean_mask, color_variation)
    color_map[ocean_mask] = apply_variation(ocean_color, ocean_mask, color_variation)
    color_map[beach_mask] = apply_variation(beach_color, beach_mask, color_variation)
    color_map[plain_mask] = apply_variation(plain_color, plain_mask, color_variation)
    color_map[forest_mask] = apply_variation(forest_color, forest_mask, color_variation)
    color_map[mountain_mask] = apply_variation(mountain_color, mountain_mask, color_variation)
    color_map[snow_mountain_mask] = apply_variation(snow_mountain_color, snow_mountain_mask, color_variation)
    
    # Плавные переходы между биомами
    transition_width = 0.02
    
    transitions = [
        (deep_ocean_height, deep_ocean_color, ocean_color),
        (ocean_height, ocean_color, beach_color),
        (beach_height, beach_color, plain_color),
        (plain_height, plain_color, forest_color),
        (forest_height, forest_color, mountain_color),
        (mountain_height, mountain_color, snow_mountain_color)
    ]
    
    for height_val, color1, color2 in transitions:
        transition_mask = (height_map >= height_val - transition_width) & (height_map < height_val + transition_width)
        if np.any(transition_mask):
            factor = (height_map[transition_mask] - (height_val - transition_width)) / (2 * transition_width)
            base_color = np.array(color1) * (1 - factor[..., np.newaxis]) + np.array(color2) * factor[..., np.newaxis]
            # Применяем вариацию к переходной зоне
            variation_factor = 1.0 + color_variation[transition_mask] * 0.5
            varied_color = base_color * variation_factor[..., np.newaxis]
            color_map[transition_mask] = np.clip(varied_color, 0, 255).astype(np.uint8)
    
    return color_map

# Генерация данных
height_map = generate_height_map(width, height, scale, octaves, persistence, lacunarity, seed)
color_variation = generate_color_variation(width, height, color_noise_scale, color_noise_intensity, seed)
color_map = height_to_color(height_map, color_variation)

# Сохранение и отображение
image = Image.fromarray(color_map)
image.save("land.png")

plt.imshow(color_map)
plt.axis("off")
plt.show()