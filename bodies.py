from math import hypot
class air_body:
    def __init__(self, x, y, vx, vy, ax, ay):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ax = ax
        self.ay = ay
        self.initial_speed = hypot(vx, vy)

    def calc_move(self, dt):
        # Сохраняем исходную скорость
        original_vx = self.vx
        original_vy = self.vy

        # Применяем ускорение к скорости
        new_vx = original_vx + self.ax * dt
        new_vy = original_vy + self.ay * dt

        # Ограничиваем скорость до начального значения
        current_speed = hypot(new_vx, new_vy)
        if current_speed > self.initial_speed:
            scale = self.initial_speed / current_speed
            new_vx *= scale
            new_vy *= scale
        
        self.ax = (new_vx - self.vx) / dt
        self.ay = (new_vy - self.vy) / dt

        # Рассчитываем перемещение как среднюю скорость * dt
        avg_vx = (original_vx + new_vx) / 2
        avg_vy = (original_vy + new_vy) / 2
        self.x += avg_vx * dt
        self.y += avg_vy * dt

        # Обновляем скорость
        self.vx = new_vx
        self.vy = new_vy

class missile(air_body):
    def __init__(self, x, y, vx, vy, law, target, N):
        super().__init__(x, y, vx, vy, 0., 0.)
        self.law = law
        self.target = target
        self.N = N
        
    def calc_move(self, dt):
        self.ax, self.ay = self.law.calc_a(self.target, self, self.N)
        if self.initial_speed > 1e-9:
            self.initial_speed -= hypot(self.ax, self.ay) * dt * 0.07
        else:
            self.initial_speed = 0.
            return
        super().calc_move(dt)
