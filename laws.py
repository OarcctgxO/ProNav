from math import atan2, hypot, pi
from numpy import sign, clip
from numba import njit
import const, bodies

t_norm = 1

@njit
def norm_a(vx: float, vy: float, a: float) -> list[float]:
    """Раскладывает ускорение объекта на составляющие так, что они перпендикулярны скорости.

    Args:
        vx (float): проекция скорости на ось OX
        vy (float): проекция скорости на ось OY
        a (float): перпендикулярное скорости ускорение, направление зависит от знака: + налево, - направо

    Returns:
        list[float]: список из проекций ускорения на оси OX и OY
    """
    vp = hypot(vx, vy)
    if vp < const.eps:
        return [0.0, 0.0]
    vp += const.eps
    ax = -a * (vy / vp)
    ay = a * (vx / vp)
    return [ax, ay]

@njit
def join_a(vx: float, vy: float, ax: float, ay: float) -> float:
    """Обратная операция к norm_a - собирает ускорение в одну переменную, перпендикулярную к скорости, направление зависит от знака: + налево, - направо

    Args:
        vx (float): проекция скорости на ось OX
        vy (float): проекция скорости на ось OY
        ax (float): проекция ускорения на ось OX
        ay (float): проекция ускорения на ось OY

    Returns:
        float: абсолютное ускорение, перпендикулярное скорости, направление зависит от знака: + налево, - направо
    """
    return hypot(ax, ay) * sign(vx * ay - vy * ax)

@njit
def vc(dx:float, dy:float, dvx:float, dvy:float) -> float:
    """Абсолютная скорость сближения объектов, знак положителен при сближении

    Args:
        dx (float): разность координат x
        dy (float): разность координат y
        dvx (float): разность проекций скорости на OX
        dvy (float): разность проекций скорости на OY

    Returns:
        float: абсолютная скорость сближения, знак положителен при сближении
    """
    v = hypot(dvx, dvy) * sign(- dvx * dx - dvy * dy)
    return v
    
def PP(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """Pure Pursuit - простейший (и худший) из представленных законов.
    Боковое усилие пропорционально разности углов между скоростью ракеты и направлением на цель.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    d = hypot(x, y)
    if d < const.eps:
        return 0.0
    
    vp = hypot(pursuer.vx, pursuer.vy)

    target_angle = atan2(y, x)
    velocity_angle = atan2(pursuer.vy, pursuer.vx)
    angle_diff = target_angle - velocity_angle
    
    angle_diff = (angle_diff + pi) % (2 * pi) - pi
    
    a = N * (angle_diff * vp) / t_norm
    
    return a

def TPN(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """True Proportional Navigation - один из самых простых законов PN семейства.
    Боковое усилие пропорционально скорости изменения направления на цель.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    
    if hypot(x, y) <= const.eps:
        return 0.0

    los_rate = (vy * x - vx * y) / (x**2 + y**2)
    vp = hypot(pursuer.vx, pursuer.vy)
    
    a = los_rate * vp * N
    
    return a

def APN(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """Augmented Proportional Navigation - дополнение для TPN, добавляет учет ускорения угла направления на цель.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    ax = target.ax - pursuer.ax
    ay = target.ay - pursuer.ay
    
    if hypot(x, y) <= const.eps:
        return 0.0

    los_rate = (vy * x - vx * y) / (x**2 + y**2)
    vp = hypot(pursuer.vx, pursuer.vy)
    
    numerator = vy * x - vx * y
    denominator = x**2 + y**2 + const.eps
    
    d_numerator = ay * x - ax * y
    d_denominator = 2 * (x * vx + y * vy)
    
    alpha_los = (d_numerator * denominator - numerator * d_denominator) / (denominator ** 2)
    
    a = (los_rate + 0.5 * alpha_los * t_norm) * vp * N
    return a

def ZEMPN(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """Zero Effort Miss Proportional Navigation - закон просчитывает промах нулевого усилия (расстояние промаха, если ракета и цель бездействуют).
    Боковое усилие пропорционально промаху.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy

    if hypot(x, y) < const.eps or hypot(pursuer.vx, pursuer.vy) < const.eps:
        return 0.0

    numerator = x * vx + y * vy
    denominator = vx**2 + vy**2 + const.eps
    tgo = -numerator / denominator

    ZEMx = x + vx * tgo
    ZEMy = y + vy * tgo

    # Нормаль к скорости ракеты (перпендикуляр)
    norm_x = -pursuer.vy
    norm_y = pursuer.vx
    norm_length = hypot(norm_x, norm_y)
    if norm_length < const.eps:
        return 0.0

    # Проекция ZEM на нормаль
    ZEM_proj = (ZEMx * norm_x + ZEMy * norm_y) / norm_length

    tgo_sq = tgo**2 + const.eps
    a = (N * ZEM_proj) / tgo_sq

    return a

def ZEMAPN(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """Zero Effort Miss Augmented Proportional Navigation - закон пока пересматривается.
    Боковое усилие пропорцинально промаху.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    ax = target.ax
    ay = target.ay
    r = hypot(x, y)
    
    if r < const.eps or hypot(pursuer.vx, pursuer.vy) < const.eps:
        return 0.0

    numerator = x * vx + y * vy
    denominator = vx**2 + vy**2 + const.eps
    tgo = -numerator / denominator
    
    ZEMx = x + vx * tgo + 0.5 * ax * tgo**2
    ZEMy = y + vy * tgo + 0.5 * ay * tgo**2

    norm_x = -pursuer.vy
    norm_y = pursuer.vx
    norm_length = hypot(norm_x, norm_y)
    
    if norm_length < const.eps:
        return 0.0
    
    ZEM_proj = (ZEMx * norm_x + ZEMy * norm_y) / norm_length
    tgo_sq = tgo**2 + const.eps

    return (N * ZEM_proj) / tgo_sq

def myZEM(target: "bodies.Airplane", pursuer: "bodies.Missile", N: int, dt: float) -> float:
    """Мой вариант ZEMPN закона. Ракета переходит в свою систему отсчета, находит пересечение траектории цели с OY, поворачивает ракету, чтобы в этой точке ракета и цель оказались одновременно.
    Боковое усилие пропорционально промаху.

    Args:
        target (bodies.Airplane): перехватываемая цель
        pursuer (bodies.Missile): ракета
        N (int): навигационная постоянная
        dt (float): шаг симуляции (не используется)

    Returns:
        float: управляющее боковое усилие
    """
    xt, yt, vxt, vyt = target.x, target.y, target.vx, target.vy
    xp, yp, vxp, vyp = pursuer.x, pursuer.y, pursuer.vx, pursuer.vy
    #меняем систему координат
    xt_shifted = xt - xp
    yt_shifted = yt - yp
    vp = hypot(vxp, vyp)
    cost, sint = vyp / vp, -vxp / vp
    xt_new = xt_shifted * cost + yt_shifted * sint
    yt_new = -xt_shifted * sint + yt_shifted * cost
    vxt_new = vxt * cost + vyt * sint
    vyt_new = -vxt * sint + vyt * cost
    vxp_new = 0
    
    xt, yt, vxt, vyt, xp, yp, vxp, vyp = xt_new, yt_new, vxt_new, vyt_new, 0.0, 0.0, vxp_new, vp
    
    if abs(vxt) < const.eps:
        return TPN(target, pursuer, N, dt)
    tgo = - xt / vxt
    tgo = clip(tgo, const.eps, 999999)
    yc = yt + vyt * tgo
    ZEM = yc - vyp * tgo
    
    a = N * ZEM * sign(xt) * sign(- xt / vxt) / (tgo**2 + const.eps)
    return a