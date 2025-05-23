import matplotlib
matplotlib.use("TkAgg")
import tkinter as tk
from tkinter import ttk
from bodies import *
from plotter import *
from const import acceleration_pressed, FPS
import laws

class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.simulation_running = False
        self.plotter = None
        self.keys_pressed = {}
        self.after_ids = []
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_key_bindings()

    def on_close(self):
        self.stop_simulation()
        self.root.destroy()
        matplotlib.pyplot.close("all")

    def setup_ui(self):
        self.root.title("Симуляция наведения ракеты")

        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(control_frame, text="Закон наведения:").pack()
        self.guidance_law = ttk.Combobox(
            control_frame, values=["PP", "TPN", "APN", 'ZEMPN', 'ZEMAPN'], state="readonly"
        )
        self.guidance_law.set("PP")
        self.guidance_law.pack(pady=5)

        self.start_button = ttk.Button(
            control_frame, text="Старт", command=self.start_simulation
        )
        self.start_button.pack(pady=10)

        self.pause_button = ttk.Button(
            control_frame,
            text="Пауза",
            state=tk.DISABLED,
            command=self.pause_simulation,
        )
        self.pause_button.pack()

        self.stop_button = ttk.Button(
            control_frame, text="Стоп", state=tk.DISABLED, command=self.stop_simulation
        )
        self.stop_button.pack()

        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.plot_frame.configure(takefocus=True)
        self.plot_frame.focus_set()
        self.plot_frame.bind("<Button-1>", lambda e: self.plot_frame.focus_force())

        self.plotter = SimulationPlotter(self.plot_frame)

    def setup_key_bindings(self):
        self.plot_frame.bind("<KeyPress>", self.on_key_press)
        self.plot_frame.bind("<KeyRelease>", self.on_key_release)
        self.plot_frame.focus_set()

    def on_key_press(self, event):
        key = event.keycode
        self.keys_pressed[key] = True
        self.update_acceleration()

    def on_key_release(self, event):
        key = event.keycode
        if key in self.keys_pressed:
            del self.keys_pressed[key]
        self.update_acceleration()

    def update_acceleration(self):
        if hasattr(self, "aircraft"):
            self.aircraft.ax = 0
            self.aircraft.ay = 0
            self.aircraft.ax_result = 0
            self.aircraft.ay_result = 0
            
            if ord("A") in self.keys_pressed:
                self.aircraft.ax = -acceleration_pressed
            if ord("D") in self.keys_pressed:
                self.aircraft.ax = acceleration_pressed
            if ord("W") in self.keys_pressed:
                self.aircraft.ay = acceleration_pressed
            if ord("S") in self.keys_pressed:
                self.aircraft.ay = -acceleration_pressed

    def start_simulation(self):
        if self.simulation_running:
            return
        self.plotter.ax.set_title("Симуляция наведения", color="black")
        self.simulation_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL)
        self.guidance_law.config(state=tk.DISABLED)
        self.plotter.reset_trajectories()

        self.aircraft = airplane(
            x=20.0, 
            y=20.0, 
            vx=-5., 
            vy=0.0, 
            ax=0.0, 
            ay=0.0)

        self.missile = missile(
            x=0.0,
            y=0.0,
            vx=10.0,
            vy=0.0,
            target=self.aircraft,
            law=getattr(laws, self.guidance_law.get()),
            N = 3
        )

        self.plot_frame.focus_set()
        self.run_simulation()

    def stop_simulation(self):
        self.simulation_running = False
        for after_id in self.after_ids:
            self.root.after_cancel(after_id)
        self.after_ids.clear()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.guidance_law.config(state=tk.NORMAL)

    def pause_simulation(self):
        if self.simulation_running:
            self.simulation_running = False
        else:
            self.simulation_running = True
            self.plot_frame.focus_set()
            self.run_simulation()
    
    def win(self):
        self.plotter.ax.set_title("Победа!", color="Green")
        self.plotter.canvas.draw()
        self.stop_simulation()
        
    def check_win(self):
        if self.aircraft.x ** 2 + self.aircraft.y ** 2 < 0.9:
            self.win()

    def run_simulation(self):
        if not self.simulation_running:
            return
        self.root.update_idletasks()
        self.root.update()
        dt = 1 / FPS

        try:
            self.update_acceleration()
            self.aircraft.calc_move(dt)
            self.missile.calc_move(dt)

            self.plotter.update_plot(self.aircraft, self.missile)

            distance = (
                (self.missile.x - self.aircraft.x) ** 2
                + (self.missile.y - self.aircraft.y) ** 2
            ) ** 0.5
            if distance < 0.2:
                self.plotter.ax.set_title("Цель поражена!", color="red")
                self.plotter.canvas.draw()
                self.stop_simulation()
                return

            new_id = self.root.after(int(dt * 1000), self.run_simulation)
            self.after_ids = [new_id]
            self.check_win()

        except Exception as e:
            print(f"Ошибка: {e}")
            self.stop_simulation()


def main():
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()