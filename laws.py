from math import atan2, sqrt, hypot, pi
import numpy as np
class law:
    @staticmethod
    def calc_a(pursuer, target, N):
        return [0.0, 0.0]
class TPN(law):
    @staticmethod
    def calc_a(pursuer, target, N):
        # координаты цели относительно ракеты
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        vx = target.vx - pursuer.vx
        vy = target.vy - pursuer.vy
        if hypot(x, y) <= 1e-6:
            return[0.0, 0.0]

        los_rate = (vy * x - vx * y) / (x**2 + y**2)
        vp = sqrt(pursuer.vx**2 + pursuer.vy**2)
        if vp <= 1e-6:
            return [0.0, 0.0]
        a = los_rate * vp * N
        calc_ax = -a * (pursuer.vy / vp)
        calc_ay = a * (pursuer.vx / vp)
        return [calc_ax, calc_ay]

class PP(law):
    @staticmethod
    def calc_a(pursuer, target, N):
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        
        r_norm = hypot(x, y)
        if r_norm < 1e-6:
            return [0.0, 0.0]
        
        vp = hypot(pursuer.vx, pursuer.vy)
        if vp < 1e-6:
            return [0.0, 0.0]

        target_angle = atan2(y, x)
        velocity_angle = atan2(pursuer.vy, pursuer.vx)
        angle_diff = target_angle - velocity_angle
        
        angle_diff = (angle_diff + pi) % (2 * pi) - pi
        
        a_perp = N * (angle_diff * vp / 1)
        ax = -a_perp * pursuer.vy / vp
        ay =  a_perp * pursuer.vx / vp
        
        return [ax, ay]
    
class APN(TPN):
    @staticmethod
    def calc_a(pursuer, target, N):
        ax, ay = TPN.calc_a(pursuer, target, N)
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        
        r_squared = x**2 + y**2
        if r_squared < 1e-6:
            return [ax, ay]
        
        a_dot_r = target.ax * x + target.ay * y
        ax_add = target.ax - (a_dot_r * x) / r_squared
        ay_add = target.ay - (a_dot_r * y) / r_squared
        
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
    def calc_a(pursuer, target, N):
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        vx = target.vx - pursuer.vx
        vy = target.vy - pursuer.vy
        
        epsilon = 1e-6
        numerator = x * vx + y * vy
        denominator = vx**2 + vy**2 + epsilon
        tgo = -numerator / denominator
        
        ZEMx = x + vx * tgo
        ZEMy = y + vy * tgo
        
        tgo_sq = tgo**2 + epsilon
        ax_orig = (N * ZEMx) / tgo_sq
        ay_orig = (N * ZEMy) / tgo_sq
        
        vp_x, vp_y = pursuer.vx, pursuer.vy
        dot = ax_orig * vp_x + ay_orig * vp_y
        mag_vp_sq = vp_x**2 + vp_y**2 + epsilon
        ax = ax_orig - (dot / mag_vp_sq) * vp_x
        ay = ay_orig - (dot / mag_vp_sq) * vp_y
        
        return [ax, ay]
    
class ZEMAPN(law):
    @staticmethod
    def calc_a(pursuer, target, N):
        x = target.x - pursuer.x
        y = target.y - pursuer.y
        vx = target.vx - pursuer.vx
        vy = target.vy - pursuer.vy
        ax = target.ax
        ay = target.ay
        
        epsilon = 1e-6
        numerator = x * vx + y * vy
        denominator = vx**2 + vy**2 + epsilon
        tgo = -numerator / denominator
        
        ZEMx = x + vx * tgo + 0.5 * ax * tgo**2
        ZEMy = y + vy * tgo + 0.5 * ay * tgo**2
        
        tgo_sq = tgo**2 + epsilon
        ax_orig = (N * ZEMx) / tgo_sq
        ay_orig = (N * ZEMy) / tgo_sq
        
        vp_x, vp_y = pursuer.vx, pursuer.vy
        dot = ax_orig * vp_x + ay_orig * vp_y
        mag_vp_sq = vp_x**2 + vp_y**2 + epsilon
        ax = ax_orig - (dot / mag_vp_sq) * vp_x
        ay = ay_orig - (dot / mag_vp_sq) * vp_y
        
        return [ax, ay]