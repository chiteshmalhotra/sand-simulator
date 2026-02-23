# PySand: A Cellular Automata Sandbox

**PySand** is a real-time 2D physics simulation built with Python and Pygame. It simulates the behavior of different materials—solids, liquids, and gases—based on density and state-of-the-art cellular automata rules.

Default view
<img width="1075" height="882" alt="default" src="https://github.com/user-attachments/assets/0ba049e7-5790-4383-a682-c32b06982951" />

Dark theme + debug mode
<img width="1075" height="882" alt="darkmode_with_debugmenu" src="https://github.com/user-attachments/assets/dab6a9dc-bcca-48f7-bd9a-d20e8abed4cf" />

## 🚀 Features

* **Diverse Materials**: Each block has unique properties including density, state (solid, liquid, gas), and special abilities (e.g., Acidic destruction).
* **Dynamic Physics**
* **Grains (Sand)**: Fall and pile up based on gravity.
* **Liquids (Water, Acid)**: Flow horizontally and fill containers.
* **Gases (Steam)**: Rise and diffuse upwards.


* **Optimized Rendering**: Uses an "Active Grid" system to only process blocks that need to move, improving performance.
* **Debug Suite**: Real-time FPS monitoring, active block counts, and grid-line overlays.
* **Dual Themes**: Switch between Dark and Light modes on the fly.

---

## 🛠️ Controls

### Mouse

* **Left Click**: Place selected material.
* **UI Interaction**: Click buttons in the sidebar to toggle simulation settings.

### Keyboard

* `0`: Air (Eraser)
* `1`: Sand
* `2`: Stone
* `3`: Water
* `4`: Acid
* `5`: Steam


* **Space / Enter**: Pause/Resume the simulation.

---

## 🧬 Simulation Logic

The simulation operates on a grid-based movement system. Every frame, the engine checks the "Density" of a block and its neighbors to decide if a swap should occur.

| Material | State | Density | Behavior |
| --- | --- | --- | --- |
| **Stone** | Solid | 6 | Static; does not move. |
| **Sand** | Grain | 4 | Falls down; slides off slopes. |
| **Water** | Liquid | 2 | Falls down; spreads left and right. |
| **Acid** | Liquid | 9 | Heavy liquid; destroys materials it touches. |
| **Steam** | Gas | 0 | Rises up and diffuses. |

---

## 📦 Installation

1. **Prerequisites**: Ensure you have Python 3.x installed.
2. **Install Dependencies**:
```bash
pip install pygame numpy

```


3. **Run the Game**:
```bash
python main.py

```



---

## 🏗️ Future Roadmap

* [ ] **Heat Exchange**: Adding temperature variables to turn water into steam or lava into stone.
* [ ] **Chunking**: Further optimization for larger screen sizes.
* [ ] **Multi-Brush**: Larger brush sizes for faster world building.
