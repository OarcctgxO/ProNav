from numpy import clip

import const
import laws

class Airplane:
    def __init__(self, x, y, vx, vy, air_drag):
        self.x = x  # координата x
        self.y = y  # координата y
        self.vx = vx  # проекция скорости на ось x
        self.vy = vy  # проекция скорости на ось y

        self.an = 0.0
        self.at = 0.0
        self.ax, self.ay = laws.norm_a(self.vx, self.vy, self.an)

        self.max_speed = const.airplane_max_speed
        self.current_speed = const.hypotenuse(self.vx, self.vy)
        self.air_drag = air_drag

    def calc_move(self, dt):
        self.ax, self.ay = laws.norm_a(self.vx, self.vy, self.an)

        self.current_speed += self.at * dt - const.hypotenuse(self.ax, self.ay) * dt * self.air_drag

        if self.current_speed < const.eps:
            self.current_speed = 0.0
            return
        
        self.current_speed = clip(self.current_speed, 1, self.max_speed)
        
        # Применяем ускорение к скорости
        new_vx = self.vx + self.ax * dt
        new_vy = self.vy + self.ay * dt

        speed_after_turn = const.hypotenuse(new_vx, new_vy)

        scale = self.current_speed / speed_after_turn
        new_vx *= scale
        new_vy *= scale

        # Считаем "реальное" ускорение (для методов наведения с учетом ускорения цели)
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


class Missile(Airplane):
    def __init__(self, x, y, vx, vy, air_drag, law, target, N):
        super().__init__(x, y, vx, vy, air_drag)
        self.law = law  # закон наведения на цель
        self.target = target  # сама цель
        self.N = N  # коэффициент пропорциональности наведения
        self.max_speed = self.current_speed
        
    def calc_move(self, dt):
        # считаем ускорение для перехвата цели (по одному из законов). ускорение в 2 раза больше максимального ускорения самолета
        self.an = clip(
            self.law(self.target, self, self.N, dt),
            -2 * const.acceleration_n,
            2 * const.acceleration_n,
        )
        super().calc_move(dt)
