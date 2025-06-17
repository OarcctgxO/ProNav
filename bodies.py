from math import hypot
from const import eps, air_drag
from laws import norm_a
from filter import AccelerationFilter
from numpy import clip

from main import acceleration_pressed
class airplane:
    def __init__(self, x, y, vx, vy):
        self.x = x  #координата x
        self.y = y  #координата y
        self.vx = vx    #проекция скорости на ось x
        self.vy = vy    #проекция скорости на ось y

        self.a = 0.
        self.ax, self.ay = norm_a(self.vx, self.vy, self.a)
        
        self.max_speed = hypot(vx, vy)  #максимальная скорость определяется как начальная

    def calc_move(self, dt):    #метод двигает самолет и записывает его положение через dt времени
        # Считаем проекции ускорения
        self.ax, self.ay = norm_a(self.vx, self.vy, self.a)
        # Применяем ускорение к скорости
        new_vx = self.vx + self.ax * dt
        new_vy = self.vy + self.ay * dt

        # Ограничиваем скорость до максимума
        current_speed = hypot(new_vx, new_vy)
        if current_speed > self.max_speed:
            scale = self.max_speed / current_speed
            new_vx *= scale
            new_vy *= scale
        
        #Считаем "реальное" ускорение (для методов наведения с учетом ускорения цели)
        self.ax = (new_vx - self.vx) / dt
        self.ay = (new_vy - self.vy) / dt

        # Рассчитываем перемещение как среднюю скорость * dt
        avg_vx = (self.vx + new_vx) / 2
        avg_vy = (self.vy + new_vy) / 2
        self.x += avg_vx * dt
        self.y += avg_vy * dt

        # Обновляем скорость
        self.vx = new_vx
        self.vy = new_vy

class missile(airplane):    #ракета почти ничем не отличается от самолета
    def __init__(self, x, y, vx, vy, law, target, N, alpha):
        super().__init__(x, y, vx, vy)
        self.law = law  #закон наведения на цель
        self.target = target    #сама цель
        self.N = N  #коэффициент пропорциональности наведения
        self.filter = AccelerationFilter(alpha)
        
    def calc_move(self, dt):
        #считаем ускорение для перехвата цели (по одному из законов). ускорение в 2 раза больше максимального ускорения самолета
        self.a = clip(self.law(self.target, self, self.N), -2* acceleration_pressed, 2* acceleration_pressed)
        if self.max_speed > eps:
            self.max_speed -= hypot(self.ax, self.ay) * dt * air_drag   #замедляемся пропорционально боковому усилию поворота
        else:
            self.max_speed = 0.
            return
        super().calc_move(dt)
