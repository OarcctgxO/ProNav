from math import atan2, sqrt, hypot, pi
from const import eps, K_a
from numpy import sign


def norm_a(vx, vy, a):
    vp = hypot(vx, vy)
    if vp < eps:
        return [0.0, 0.0]
    vp += eps
    ax = -a * (vy / vp)
    ay = a * (vx / vp)
    return [ax, ay]

def TPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy
    
    if hypot(x, y) <= eps:
        return[0.0, 0.0]

    los_rate = (vy * x - vx * y) / (x**2 + y**2)
    vp = hypot(pursuer.vx, pursuer.vy)
    
    a = los_rate * vp * N
    
    return norm_a(pursuer.vx, pursuer.vy, a)

def PP(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    if hypot(x, y) < eps:
        return [0.0, 0.0]
    
    vp = hypot(pursuer.vx, pursuer.vy)

    target_angle = atan2(y, x)
    velocity_angle = atan2(pursuer.vy, pursuer.vx)
    angle_diff = target_angle - velocity_angle
    
    angle_diff = (angle_diff + pi) % (2 * pi) - pi
    
    a = N * (angle_diff * vp)
    
    return norm_a(pursuer.vx, pursuer.vy, a)

def APN(target, pursuer, N):
    ax, ay = TPN(target, pursuer, N)
    x = target.x - pursuer.x
    y = target.y - pursuer.y

    r = hypot(x, y)
    if r < eps:
        return [ax, ay]

    K = min(K_a / r, 1)

    a = N * 0.5 * (- target.ax * K * x + target.ay * K * y ) / r

    add_a = norm_a(pursuer.vx, pursuer.vy, a)

    return [ax + add_a[0], ay + add_a[1]]

def ZEMPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy

    if hypot(x, y) < eps or hypot(pursuer.vx, pursuer.vy) < eps:
        return [0. , 0.]

    numerator = x * vx + y * vy
    denominator = vx**2 + vy**2 + eps
    tgo = -numerator / denominator

    ZEMx = x + vx * tgo
    ZEMy = y + vy * tgo

    tgo_sq = tgo**2 + eps

    ax_orig = (N * ZEMx) / tgo_sq
    ay_orig = (N * ZEMy) / tgo_sq
    # для направления по перпендикуляру к скорости
    a = hypot(ax_orig, ay_orig) * sign(pursuer.vx * ay_orig - pursuer.vy * ax_orig)

    return norm_a(pursuer.vx, pursuer.vy, a)

def ZEMAPN(target, pursuer, N):
    x = target.x - pursuer.x
    y = target.y - pursuer.y
    vx = target.vx - pursuer.vx
    vy = target.vy - pursuer.vy

    r = hypot(x, y)
    K = min(K_a / r, 1)
    ax = target.ax
    ay = target.ay

    if r < eps or hypot(pursuer.vx, pursuer.vy) < eps:
        return [0. , 0.]

    numerator = x * vx + y * vy
    denominator = vx**2 + vy**2 + eps
    tgo = -numerator / denominator

    ZEMx = x + vx * tgo
    ZEMy = y + vy * tgo

    ZEMx += 0.5 * ax * K * tgo**2
    ZEMy += 0.5 * ay * K * tgo**2

    tgo_sq = tgo**2 + eps
    ax_orig = (N * ZEMx) / tgo_sq
    ay_orig = (N * ZEMy) / tgo_sq

    a = hypot(ax_orig, ay_orig) * sign(pursuer.vx * ay_orig - pursuer.vy * ax_orig)

    return norm_a(pursuer.vx, pursuer.vy, a)
