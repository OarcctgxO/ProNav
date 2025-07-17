air_drag = 0.07 #коэффициент пропорциональности между боковым ускорением ракеты и ее замедлением (для реальных ракет 1-5%)
eps = 1e-6  #число, приближенное к нулю
N = 3   #навигационная постоянная ракеты

acceleration_n = 100
acceleration_t = 10
FPS = 120
scale = 7 #масштаб симуляции
move_trajectory = 1
win_zone_r = 5
plane_size = 2
#НАЧАЛЬНЫЕ УСЛОВИЯ: x, y, vx, vy
airplane_start = [400.0, 400.0, -50.0, 0.0, air_drag]
missile_start = [0.0, 0.0, 100.0, 0.0, air_drag]

airplane_max_speed = 50.0