# G-Code Grid Maker v1.2

A Python-based G-code generator, visualizer, and simulator for laser engravers and CNC routers.  
Built with 💡 Tkinter + math + maker frustration.

Ideal for 3020 CNC routers, diode lasers, and anyone needing a quick and visual way to produce consistent grid-style toolpaths for engraving, probing, or pattern work.

---

## 🚀 Features

- 🔁 **Dual Operation Modes**:
  - **Laser Mode**: uses `M3`, `M5`, and S-values (0–255)
  - **CNC Mode**: uses safe Z retracts, plunge cuts, and `M3` spindle logic (S-values 0–1000)
  
- 📐 **Grid Toolpath Generator**:
  - Choose between **Raster** or **Zig-Zag** scanning patterns
  - Fully configurable X/Y area and grid resolution

- 🧠 **G-Code Generator**:
  - Outputs clean, GRBL-compatible G-code
  - Optional: add `$H` homing and `G92` or `G10` origin-setting commands
  - Auto-converts power % into proper `S` values based on mode

- 🎥 **Path Simulation**:
  - Real-time playback of toolpaths
  - Visual dot for active position
  - Color-coded travel and cutting moves
  
- 🧭 **Visual Feedback**:
  - Scalable canvas with automatic redrawing
  - Live grid preview, ruler overlays, and movement direction
  
- 💾 **Save G-code to File**:
  - Export as `.nc`, `.tap`, `.ngc`, `.txt` and more

---

## 📸 Screenshots

![image](https://github.com/user-attachments/assets/f6e76757-0fad-4b85-b5e0-f3a3d76fbc62)



Sample layout showing raster scan, laser cut lines in red, travel in blue, and a green simulation dot.

---

## 🛠 Requirements

- Python 3.6+
- Tkinter (usually bundled with Python on Windows/macOS)

> On Debian-based Linux, install with:
> ```bash
> sudo apt install python3-tk
> ```

---

## ⚙️ How to Run

1. Clone or download this repo:
   ```bash
   git clone https://github.com/your-username/gcode-grid-maker.git
   cd gcode-grid-maker
2. Windows exe made with pyinstaller
   download and run Cnc_GUI.exe

