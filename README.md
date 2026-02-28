Got it. Here’s a **cleaner, tighter README**. Shorter, calmer, and very “this is a dev project, not a startup pitch”.

---

# Sand Simulator 3000

A falling-sand style simulation written in Python using Pygame and NumPy.

You can place different materials on a grid and watch them interact based on simple rules like gravity, density, and allowed movement directions. The simulation uses a chunk system so only active areas are updated each frame.

---
### Latest Images

<img width="336" height="249" alt="normalmode_28feb2026" src="https://github.com/user-attachments/assets/5f61fbb7-8cf7-4de7-a346-ab9cbe0b2619" />

<img width="336" height="249" alt="darkmode_with_debugmode_28feb2026" src="https://github.com/user-attachments/assets/aa93c8ef-3abd-4524-845a-cd58abc1eab2" />

### Previous Images

<img width="358" height="294" alt="normalmode_23feb2026" src="https://github.com/user-attachments/assets/0ba049e7-5790-4383-a682-c32b06982951" />

<img width="358" height="294" alt="darkmode_with_debugmode_23feb2026" src="https://github.com/user-attachments/assets/dab6a9dc-bcca-48f7-bd9a-d20e8abed4cf" />

---

## Features

* Chunk-based simulation for performance
* Multiple materials with different behavior:
  * Sand
  * Water
  * Stone
  * Acid
  * Lava
  * Steam

* Brush sizes (small, medium, large)
* Mouse painting with variation
* Keyboard shortcuts
* Debug mode with active chunk and block visualization
* Light / dark theme toggle
* Minimal UI with tooltips

---

## Controls

### Mouse

* Left click / drag – Place blocks

### Keyboard

* Space – Pause / resume
* T – Toggle theme
* D – Toggle debug mode
* Backspace – Clear grid

### Blocks

* Number keys 0–6 – Select block type

### Brush size

* S – Small
* M – Medium
* L – Large

---

## Debug Mode

Debug mode shows:

* Active chunks
* Active blocks
* FPS, active chunk count, and active block count

Useful for understanding performance and simulation behavior.

---

## How It Works (Brief)

* The world is a grid of blocks
* The grid is divided into chunks
* Only active chunks are simulated and redrawn
* Blocks activate nearby blocks and chunks when they move
* Movement depends on material density and allowed directions

---

## Requirements

* Python 3.x
* Pygame
* NumPy

Install dependencies:

```bash
pip install pygame numpy
```

---

## Run

```bash
python main.py
```

---

## Notes

This is a learning and experimentation project which is being worked on as hobby.
Currently in early phases. So the focus is on simulation logic and performance, not polish.
If you experience some issue pls contact me.

---

## Known Issues

Minor input latency
Mouse clicks and button actions may feel slightly delayed during heavy simulation. This happens because simulation and rendering are done in the same frame.

Performance drops with large active areas
When many chunks become active at once, FPS can drop, especially on lower-end systems.

No save / load support
The simulation state is not persistent. Clearing or closing the app resets everything.

Single-threaded simulation
All logic runs on the main thread. There is no background processing.

No mobile or touch support
Designed for desktop mouse and keyboard only.

Limited material interactions
Material behavior is intentionally simple. Some interactions may look unrealistic.

UI scaling is fixed
The interface is not responsive to window resizing.
