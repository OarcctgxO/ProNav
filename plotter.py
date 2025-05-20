import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk

class SimulationPlotter:
    def __init__(self, master=None):
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        
        if master:
            self.canvas = FigureCanvasTkAgg(self.fig, master=master)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.setup_plot()
        self.aircraft_path = []
        self.missile_path = []
        
    def setup_plot(self):
        self.ax.clear()
        self.ax.set_xlim(-1, 21)
        self.ax.set_ylim(-1, 21)
        self.ax.grid(True)
        self.ax.set_title("Симуляция наведения")
        
        circle = plt.Circle((0, 0), 1, color='g', fill=False, linestyle='--')
        self.ax.add_patch(circle)
        
        self.aircraft_line, = self.ax.plot([], [], 'b-', alpha=0.5, label='Самолет')
        self.missile_line, = self.ax.plot([], [], 'r-', alpha=0.5, label='Ракета')
        
        self.aircraft_point = self.ax.plot([], [], 'bo', markersize=8)[0]
        self.missile_point = self.ax.plot([], [], 'ro', markersize=6)[0]
        
        self.ax.legend()
        
    def update_plot(self, aircraft, missile):
        self.aircraft_path.append([aircraft.x, aircraft.y])
        self.missile_path.append([missile.x, missile.y])

        if len(self.aircraft_path) > 1:
            self.aircraft_line.set_data(
                [p[0] for p in self.aircraft_path],
                [p[1] for p in self.aircraft_path]
            )
        if len(self.missile_path) > 1:
            self.missile_line.set_data(
                [p[0] for p in self.missile_path],
                [p[1] for p in self.missile_path]
            )
    
        self.aircraft_point.set_data([aircraft.x], [aircraft.y])
        self.missile_point.set_data([missile.x], [missile.y])
    
        self.auto_scale()
    
        if hasattr(self, 'canvas'):
            self.canvas.draw()
        else:
            plt.pause(0.01)
    
    def auto_scale(self):
        if not self.aircraft_path or not self.missile_path:
            return
        
        all_x = [p[0] for p in self.aircraft_path + self.missile_path]
        all_y = [p[1] for p in self.aircraft_path + self.missile_path]
    
        margin = 1
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        
        range_x, range_y = x_max - x_min, y_max - y_min
        
        if range_x > range_y:
            y_min -= (range_x - range_y) / 2
            y_max += (range_x - range_y) / 2
        else:
            x_min -= (range_y - range_x) / 2
            x_max += (range_y - range_x) / 2
        
        self.ax.set_xlim(x_min - margin, x_max + margin)
        self.ax.set_ylim(y_min - margin, y_max + margin)
        
    def reset_trajectories(self):
        self.aircraft_path = []
        self.missile_path = []
        self.aircraft_line.set_data([], [])
        self.missile_line.set_data([], [])
        if hasattr(self, 'canvas'):
            self.canvas.draw()