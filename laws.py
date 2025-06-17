from math import atan2, hypot, pi, sqrt, sin, cos
from const import eps, air_drag
from numpy import sign, clip


def norm_a(vx, vy, a): #раскладывает ускорение цели на составляющие так, что они перпендикулярны скорости
    vp = hypot(vx, vy)
    if vp < eps:
        return [0.0, 0.0]
    vp += eps
    ax = -a * (vy / vp)
    ay = a * (vx / vp)
    return [ax, ay]

def join_a(vx, vy, ax, ay):
    return hypot(ax, ay) * sign(vx * ay - vy * ax)

def vc(dx, dy, dvx, dvy):
    v = hypot(dvx, dvy) * sign(- dvx * dx - dvy * dy)
    return v
    

def PP(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    if hypot(x, y) < eps:
        return 0.0
    
    vp = hypot(pursuer.vx, pursuer.vy)

    target_angle = atan2(y, x)
    velocity_angle = atan2(pursuer.vy, pursuer.vx)
    angle_diff = target_angle - velocity_angle
    
    angle_diff = (angle_diff + pi) % (2 * pi) - pi
    
    a = N * (angle_diff * vp)
    
    return a

def TPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    
    if hypot(x, y) <= eps:
        return 0.0

    los_rate = (vy * x - vx * y) / (x**2 + y**2)
    vp = hypot(pursuer.vx, pursuer.vy)
    
    a = los_rate * vp * N
    
    return a

def APN(target, pursuer, N):
    a = TPN(target, pursuer, N)
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    axt, ayt = pursuer.filter.update(target.ax, target.ay)
    r = hypot(x, y)
    
    if r < eps:
        return 0.0

    nx = -y / r
    ny = x / r
    a_target_normal = axt * nx + ayt * ny

    # Адаптивный N: уменьшаем манёвры при низкой скорости
    pursuer_speed = hypot(pursuer.vx, pursuer.vy)
    adaptive_N = N * min(1.0, pursuer_speed / 10.0)  # 10.0 — пороговая скорость
    a += (adaptive_N / 2) * a_target_normal
    
    return a

def ZEMPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy

    if hypot(x, y) < eps or hypot(pursuer.vx, pursuer.vy) < eps:
        return 0.0

    numerator = x * vx + y * vy
    denominator = vx**2 + vy**2 + eps
    tgo = -numerator / denominator

    ZEMx = x + vx * tgo
    ZEMy = y + vy * tgo

    # Нормаль к скорости ракеты (перпендикуляр)
    norm_x = -pursuer.vy
    norm_y = pursuer.vx
    norm_length = hypot(norm_x, norm_y)
    if norm_length < eps:
        return 0.0

    # Проекция ZEM на нормаль
    ZEM_proj = (ZEMx * norm_x + ZEMy * norm_y) / norm_length

    tgo_sq = tgo**2 + eps
    a = (N * ZEM_proj) / tgo_sq

    return a

def ZEMAPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    axt, ayt = pursuer.filter.update(target.ax, target.ay)
    r = hypot(x, y)
    
    if r < eps or hypot(pursuer.vx, pursuer.vy) < eps:
        return 0.0

    # Прогнозируем tgo с учётом текущего замедления ракеты
    tgo = max(0.1, -(x * vx + y * vy) / (vx**2 + vy**2 + eps))  # Базовая оценка

    # Учёт потери скорости из-за манёвров (air_drag * a²)
    current_a = hypot(pursuer.ax, pursuer.ay)
    speed_loss = air_drag * current_a * tgo
    pursuer_speed_predicted = max(0.1, hypot(pursuer.vx, pursuer.vy) - speed_loss)

    # Корректируем ZEM с учётом прогнозируемой скорости
    ZEMx = x + vx * tgo + 0.5 * axt * tgo**2
    ZEMy = y + vy * tgo + 0.5 * ayt * tgo**2

    norm_x = -pursuer.vy
    norm_y = pursuer.vx
    norm_length = hypot(norm_x, norm_y)
    
    if norm_length < eps:
        return 0.0
    
    ZEM_proj = (ZEMx * norm_x + ZEMy * norm_y) / norm_length
    tgo_sq = tgo**2 + eps

    # Адаптивный N: уменьшаем манёвры при низкой прогнозируемой скорости
    adaptive_N = N * min(1.0, pursuer_speed_predicted / 10.0)
    return (adaptive_N * ZEM_proj) / tgo_sq

def ZEMbad(target, pursuer, N):
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
    
    if abs(vxt) < eps:
        return TPN(target, pursuer, N)
    tgo = - xt / vxt
    tgo = clip(tgo, eps, 999999)
    yc = yt + vyt * tgo
    ZEM = yc - vyp * tgo
    print(ZEM, tgo)
    
    a = N * ZEM * sign(xt) * sign(- xt / vxt) / (tgo**2 + eps)
    return clip(a, -10, 10)