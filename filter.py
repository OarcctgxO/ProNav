class AccelerationFilter:
    def __init__(self, alpha=0.3):
        """
        Фильтр ускорений цели на основе экспоненциального сглаживания.
        
        Параметры:
        - alpha: коэффициент сглаживания (0 < alpha < 1). 
          Чем меньше alpha, тем сильнее фильтрация (но больше запаздывание).
        """
        self.alpha = alpha
        self.filtered_ax = 0.0
        self.filtered_ay = 0.0

    def update(self, ax, ay):
        """
        Обновляет отфильтрованные ускорения.
        Возвращает (filtered_ax, filtered_ay).
        """
        self.filtered_ax = self.alpha * ax + (1 - self.alpha) * self.filtered_ax
        self.filtered_ay = self.alpha * ay + (1 - self.alpha) * self.filtered_ay
        return self.filtered_ax, self.filtered_ay