from math import atan2, sqrt, hypot, pi
from const import eps


def norm_a(vx, vy, a):
    vp = hypot(vx, vy)
    if vp < eps:
        return [0.0, 0.0]
    vp += eps
    ax = -a * (vy / vp)
    ay = a * (vx / vp)
    return [ax, ay]

class law:
    @staticmethod
    def calc_a(target, pursuer, N):
        return [0.0, 0.0]

class TPN(law):
    @staticmethod
    def calc_a(target, pursuer, N):
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

class PP(law):
    @staticmethod
    def calc_a(target, pursuer, N):
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

class APN(TPN):
    @staticmethod
    def calc_a(target, pursuer, N):
        ax, ay = TPN.calc_a(target, pursuer, N)
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        
        r = hypot(x, y)
        if r < eps:
            return [ax, ay]
        
        a_dot_r = target.ax * x + target.ay * y
        ax_add = target.ax - (a_dot_r * x) / r**2
        ay_add = target.ay - (a_dot_r * y) / r**2
        
        vp = hypot(pursuer.vx, pursuer.vy)
        if vp < 1e-6:
            return [ax, ay]
        
        n_x = -pursuer.vy / vp
        n_y = pursuer.vx / vp
        
        a_perp = (ax_add * n_x + ay_add * n_y)
        
        ax += (N / 2) * a_perp * n_x
        ay += (N / 2) * a_perp * n_y
        
        return [ax, ay]

class ZEMPN(law):
    @staticmethod
    def calc_a(target, pursuer, N):
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
        
        vp_x, vp_y = pursuer.vx, pursuer.vy
        dot = ax_orig * vp_x + ay_orig * vp_y
        mag_vp_sq = vp_x**2 + vp_y**2 + eps
        ax = ax_orig - (dot / mag_vp_sq) * vp_x
        ay = ay_orig - (dot / mag_vp_sq) * vp_y
        
        return [ax, ay]

class ZEMAPN(law):
    @staticmethod
    def calc_a(target, pursuer, N):
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        vx = target.vx - pursuer.vx
        vy = target.vy - pursuer.vy
        ax = target.ax
        ay = target.ay
        
        if hypot(x, y) < eps or hypot(pursuer.vx, pursuer.vy) < eps:
            return [0. , 0.]
        
        numerator = x * vx + y * vy
        denominator = vx**2 + vy**2 + eps
        tgo = -numerator / denominator
        
        ZEMx = x + vx * tgo
        ZEMy = y + vy * tgo
        
        ZEMx += 0.5 * ax * tgo**2
        ZEMy += 0.5 * ay * tgo**2
        
        tgo_sq = tgo**2 + eps
        ax_orig = (N * ZEMx) / tgo_sq
        ay_orig = (N * ZEMy) / tgo_sq
        
        vp_x, vp_y = pursuer.vx, pursuer.vy
        dot = ax_orig * vp_x + ay_orig * vp_y
        mag_vp_sq = vp_x**2 + vp_y**2 + eps
        ax = ax_orig - (dot / mag_vp_sq) * vp_x
        ay = ay_orig - (dot / mag_vp_sq) * vp_y
        
        return [ax, ay]
