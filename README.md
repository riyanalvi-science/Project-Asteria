# 🚀 Project Asteria 1.0

### Autonomous Planetary Exploration Rover — Control Framework & Simulation Engine

**Asteria** is a software prototype for an autonomous planetary exploration rover. It combines procedural terrain generation, LiDAR-based obstacle detection, autonomous navigation, mission management, environmental analysis, and episodic memory into a modular control architecture.

## ✨ Features

* 🌍 Procedurally generated, effectively infinite planetary terrain
* 📡 Four-directional LiDAR simulation
* 🧭 Autonomous obstacle avoidance and path recovery
* 🗺️ Boustrophedon area-coverage planning
* 🧠 Hierarchical mission controller
* 🌡️ Environmental risk analysis
* 💾 Episodic experience logging
* 🛡️ Automatic braking and stall recovery
* 🧪 Integrated diagnostic testing framework

## 🏗️ Architecture

The system is divided into two main layers:

```text
Asteria
├── Logical Control Layer
│   ├── Navigation
│   ├── Mission Controller
│   ├── Environment Analysis
│   ├── Coverage Planner
│   └── Memory
│
└── Simulation Layer
    ├── Procedural Terrain
    ├── Obstacles
    ├── LiDAR Simulation
    └── Simulation Runtime
```

The logical control layer is separated from the simulation/rendering layer, allowing the control algorithms to operate independently of the graphical environment.

## 🛠️ Tech Stack

* Python
* Pygame
* Procedural generation
* Finite State Machines
* LiDAR raycasting
* Autonomous navigation algorithms

## ▶️ Running the Project

Clone the repository:

```bash
git clone https://github.com/riyanalvi-science/Asteria.git
cd Asteria
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the simulation:

```bash
python asteria_sim.py
```

> Adjust the entry-point filename if your repository uses a different main script.

## 📄 Project Report

For the complete architecture, mathematical formulation, algorithms, experimental validation, and future development plans:

**[📘 Read the Full Project Report](./Project_Asteria_Report.pdf)**

## 🔭 Future Work

* Global A* navigation
* Persistent mission-memory storage
* Multi-rover swarm coordination

---

### 👨‍💻 Author

**Riyan Alvi**
Indian Institute of Science Education and Research Mohali

> **Explore. Adapt. Survive.**
