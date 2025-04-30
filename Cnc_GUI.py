import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import time

class GCodeVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("G-Code Grid Naker v1.2")
        self.root.geometry("1400x900")

        self.margin = 50
        self.travel_color = 'blue'
        self.laser_color = 'red'
        self.travel_dot_color = 'green'
        self.laser_dot_color = 'red'
        self.generate_travel_color = 'purple'
        self.generate_laser_color = 'white'

        self.simulation_running = False

        self.control_frame = tk.Frame(root, bg='#2c3e50')
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.visual_frame = tk.Frame(root, bg='#1a1a1a')
        self.visual_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.visual_frame, bg='#1a1a1a', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.sim_control_frame = tk.Frame(root, bg='#34495e')
        self.sim_control_frame.pack(side=tk.TOP, fill=tk.X)

        self.gcode_display = tk.Text(root, height=10, bg='#2c3e50', fg='#CCCCCC', insertbackground='white')
        self.gcode_display.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_controls()
        self.canvas.bind("<Configure>", self.regenerate_on_resize)

    def create_controls(self):
        self.mode_var = tk.StringVar(value="laser")
        tk.Label(self.control_frame, text="Mode", bg='#2c3e50', fg='#CCCCCC').pack(pady=2)
        mode_menu = ttk.Combobox(self.control_frame, textvariable=self.mode_var, values=["laser", "cnc"], state="readonly")
        mode_menu.pack(pady=2)
        mode_menu.bind('<<ComboboxSelected>>', self.update_mode_fields)

        self.path_var = tk.StringVar(value="Raster")
        tk.Label(self.control_frame, text="Path Pattern", bg='#2c3e50', fg='#CCCCCC').pack(pady=2)
        path_menu = ttk.Combobox(self.control_frame, textvariable=self.path_var, values=["Raster", "Zig-Zag"], state="readonly")
        path_menu.pack(pady=2)

        self.tool_diameter = self.add_label_entry("TOOL DIAMETER (mm)", "1.0")
        self.x_start = self.add_label_entry("X-START POS", "0")
        self.x_end = self.add_label_entry("X-END POS", "200")
        self.y_start = self.add_label_entry("Y-START POS", "0")
        self.y_end = self.add_label_entry("Y-END POS", "200")
        self.z_pos = self.add_label_entry("Z-POS", "0")
        self.z_top = self.add_label_entry("Z-TOP POS (CNC only)", "5")
        self.grid_size = self.add_label_entry("GRID SIZE", "10")
        self.power_percent = self.add_label_entry("POWER % (0–100)", "50")
        self.feedrate = self.add_label_entry("FEEDRATE (mm/min)", "200")

        self.home_origin_var = tk.BooleanVar()
        tk.Checkbutton(self.control_frame, text="Add $H and G92 (Home & Set Origins)", variable=self.home_origin_var, bg='#2c3e50', fg='#CCCCCC', selectcolor='#34495e').pack(pady=5)

        tk.Button(self.control_frame, text="Generate G-Code", command=self.generate_gcode, bg='#27ae60', fg='#CCCCCC').pack(pady=5, fill=tk.X)
        tk.Button(self.control_frame, text="Save G-Code", command=self.save_gcode, bg='#2980b9', fg='#CCCCCC').pack(pady=5, fill=tk.X)

        self.sim_buttons = [
            tk.Button(self.sim_control_frame, text="Run Simulation", command=self.run_simulation, bg=self.travel_color, fg='#CCCCCC'),
            tk.Button(self.sim_control_frame, text="Stop&Clear", command=self.clear_simulation, bg='#c0392b', fg='#CCCCCC')
        ]
        for btn in self.sim_buttons:
            btn.pack(side=tk.LEFT, padx=5)

        self.update_mode_fields()

    def add_label_entry(self, text, default_value=""):
        tk.Label(self.control_frame, text=text, bg='#2c3e50', fg='#CCCCCC').pack(pady=2)
        entry = tk.Entry(self.control_frame)
        entry.insert(0, default_value)
        entry.pack(pady=2)
        return entry

    def update_mode_fields(self, event=None):
        mode = self.mode_var.get()
        if mode == "laser":
            self.tool_diameter.config(state='disabled')
            self.z_top.config(state='disabled')
        else:
            self.tool_diameter.config(state='normal')
            self.z_top.config(state='normal')

    def regenerate_on_resize(self, event):
        self.generate_gcode()

    def generate_gcode(self):
        self.simulation_running = False
        try:
            self.xs = float(self.x_start.get())
            self.xe = float(self.x_end.get())
            self.ys = float(self.y_start.get())
            self.ye = float(self.y_end.get())
            self.z = float(self.z_pos.get())
            self.z_safe = float(self.z_top.get())
            self.grid_size_val = float(self.grid_size.get())
            self.power_val = int(self.power_percent.get())
            self.feedrate_val = int(self.feedrate.get())
            self.tool_diameter_val = float(self.tool_diameter.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values.")
            return
    
        mode = self.mode_var.get()
        use_cnc = (mode == "cnc")
        path_pattern = self.path_var.get()
    
        self.canvas.delete("all")
        self.path_points = []
    
        width = self.xe - self.xs
        height = self.ye - self.ys
        canvas_w = self.canvas.winfo_width() - 2 * self.margin
        canvas_h = self.canvas.winfo_height() - 2 * self.margin
        self.scale_factor = min(canvas_w / width, canvas_h / height) if width and height else 1
    
        cols = math.ceil(width / self.grid_size_val)
        rows = math.ceil(height / self.grid_size_val)
    
        # Horizontal lines
        for row in range(rows + 1):
            y = self.ys + row * self.grid_size_val
            if path_pattern == "Zig-Zag" and row % 2 == 1:
                self.path_points.append((self.xe, y, True))
                self.path_points.append((self.xs, y, False))
            else:
                self.path_points.append((self.xs, y, True))
                self.path_points.append((self.xe, y, False))
    
        # Vertical lines
        for col in range(cols + 1):
            x = self.xs + col * self.grid_size_val
            if path_pattern == "Zig-Zag" and col % 2 == 1:
                self.path_points.append((x, self.ye, True))
                self.path_points.append((x, self.ys, False))
            else:
                self.path_points.append((x, self.ys, True))
                self.path_points.append((x, self.ye, False))
    
        self.draw_grid()
        self.draw_ruler()
    
        gcode = []
        gcode.append("; Generated G-Code")
        gcode.append("; Tool Diameter: {:.2f} mm".format(self.tool_diameter_val))
        gcode.append("; Mode: {}".format(mode))
        gcode.append("G21 ; Set units to mm")

    
        if self.home_origin_var.get():
            gcode.append("G92 X0 Y0 Z0 ; Set origin")
    
        gcode.append("M5")
        power_cmd = "S{:.0f}".format((self.power_val / 100) * (1000 if use_cnc else 255))
    
        for p in self.path_points:
            if p[2]:  # travel move
                gcode.append("M5")
                if use_cnc:
                    gcode.append(f"G0 Z{self.z_safe:.2f}")
            else:  # laser/cut move
                gcode.append(f"M3 {power_cmd}")
                if use_cnc:
                    gcode.append(f"G1 Z{self.z:.2f} F{self.feedrate_val}")
            gcode.append(f"G1 X{p[0]:.2f} Y{p[1]:.2f} F{self.feedrate_val}")
    
        if use_cnc:
            gcode.append(f"G0 Z{self.z_safe:.2f}")
    
        self.gcode_display.delete(1.0, tk.END)
        self.gcode_display.insert(tk.END, "\n".join(gcode))
    

        self.draw_grid()
        self.draw_ruler()

        gcode = []
        gcode.append("; Generated G-Code")
        gcode.append("; Tool Diameter: {:.2f} mm".format(self.tool_diameter_val))
        gcode.append("; Mode: {}".format(mode))
        gcode.append("G21 ; Set units to mm")
        if self.home_origin_var.get():
            gcode.append("$H ; Home")
            gcode.append("G10 L20 P1 X0 Y0 Z0 ; Set origin safely (G54)")

        gcode.append("M5")
        power_cmd = "S{:.0f}".format((self.power_val / 100) * (1000 if use_cnc else 255))

        for p in self.path_points:
            if p[2]:  # travel move
                gcode.append("M5")
                if use_cnc:
                    gcode.append(f"G0 Z{self.z_safe:.2f}")
            else:  # laser/cut move
                gcode.append(f"M3 {power_cmd}")
                if use_cnc:
                    gcode.append(f"G1 Z{self.z:.2f} F{self.feedrate_val}")
            gcode.append(f"G1 X{p[0]:.2f} Y{p[1]:.2f} F{self.feedrate_val}")

        if use_cnc:
            gcode.append("G0 Z{:.2f}".format(self.z_safe))
        self.gcode_display.delete(1.0, tk.END)
        self.gcode_display.insert(tk.END, "\n".join(gcode))

    def draw_grid(self):
        self.canvas.delete("grid")
        for i, p in enumerate(self.path_points[:-1]):
            x1 = self.margin + p[0] * self.scale_factor
            y1 = self.canvas.winfo_height() - (self.margin + p[1] * self.scale_factor)
            x2 = self.margin + self.path_points[i + 1][0] * self.scale_factor
            y2 = self.canvas.winfo_height() - (self.margin + self.path_points[i + 1][1] * self.scale_factor)
            color = self.generate_travel_color if p[2] else self.generate_laser_color
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1 if p[2] else 2, tags="grid")

    def draw_ruler(self):
        self.canvas.delete("ruler")
        for x in range(0, int(self.xe)+1, 10):
            x_pos = self.margin + x * self.scale_factor
            self.canvas.create_line(x_pos, self.canvas.winfo_height()-self.margin, x_pos, self.canvas.winfo_height()-self.margin-5, fill="white", tags="ruler")
            if x % 50 == 0:
                self.canvas.create_text(x_pos, self.canvas.winfo_height()-self.margin+10, text=str(x), fill="white", anchor=tk.N, tags="ruler")
        for y in range(0, int(self.ye)+1, 10):
            y_pos = self.canvas.winfo_height() - (self.margin + y * self.scale_factor)
            self.canvas.create_line(self.margin, y_pos, self.margin+5, y_pos, fill="white", tags="ruler")
            if y % 50 == 0:
                self.canvas.create_text(self.margin-10, y_pos, text=str(y), fill="white", anchor=tk.E, tags="ruler")

    def run_simulation(self):
        if not hasattr(self, 'path_points'):
            return
        self.simulation_running = True
        self.canvas.delete("travel")
        dot = None
        delay = max(0.005, 60.0 / (self.feedrate_val + 1))
        for i, point in enumerate(self.path_points[:-1]):
            if not self.simulation_running:
                break
            x1 = self.margin + point[0] * self.scale_factor
            y1 = self.canvas.winfo_height() - (self.margin + point[1] * self.scale_factor)
            x2 = self.margin + self.path_points[i + 1][0] * self.scale_factor
            y2 = self.canvas.winfo_height() - (self.margin + self.path_points[i + 1][1] * self.scale_factor)
            color = self.laser_color if point[2] else self.travel_color
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2, tags="travel")
            if dot:
                self.canvas.delete(dot)
            dot_color = self.laser_dot_color if point[2] else self.travel_dot_color
            dot = self.canvas.create_oval(x2-5, y2-5, x2+5, y2+5, fill=dot_color, tags="travel")
            self.canvas.update()
            time.sleep(delay)

    def clear_simulation(self):
        self.simulation_running = False
        self.canvas.delete("travel")

    def save_gcode(self):
        gcode_text = self.gcode_display.get(1.0, tk.END)
        if not gcode_text.strip():
            messagebox.showerror("Error", "G-code is empty.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".nc",
            filetypes=[("G-Code files", "*.nc *.ncc *.ngc *.tap *.txt")]
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(gcode_text)
            messagebox.showinfo("Success", "G-code saved!")

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeVisualizer(root)
    root.mainloop()
