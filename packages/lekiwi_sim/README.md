# LeKiwi MuJoCo Simulation — LeRobot Robot Plugin (`lerobot_robot_lekiwi_sim`)

High-fidelity MuJoCo-based simulation environment for the LeKiwi robot, packaged as a **LeRobot third-party robot plugin**. Once installed, the simulated robot is available as `--robot.type=lekiwi_mujoco` in any `lerobot` CLI command.

## Features

- **🎯 Physics-Accurate Simulation**: High-fidelity MuJoCo physics engine
- **🤖 Complete Robot Model**: Omniwheel base, robotic arm, and gripper
- **📹 Camera Simulation**: Front and wrist camera feeds
- **🔌 LeRobot Plugin**: Discovered automatically — use `lerobot` CLI directly
- **⚡ Real-time Visualization**: Interactive 3D environment
- **🎮 Teleoperation Support**: Direct control via keyboard

## Installation

### Prerequisites
- Python 3.11+
- MuJoCo (automatically installed with package)
- OpenGL support for visualization

### Quick Install
```bash
# From repository root
uv pip install -e packages/lekiwi_sim/

# Or if no virtual environment exists
uv venv -p 3.11 --seed
source .venv/bin/activate
uv pip install -e packages/lekiwi_sim/
```

## Usage

### Direct LeRobot CLI Usage (Plugin Mode)

Because the package is named `lerobot_robot_lekiwi_sim`, LeRobot's plugin
discovery (`register_third_party_devices`) will import it automatically.
You can then use `--robot.type=lekiwi_mujoco` with any `lerobot` CLI tool:

```bash
# Teleoperate the simulated robot
lerobot-teleoperate --robot.type=lekiwi_mujoco

# Record episodes
lerobot-record --robot.type=lekiwi_mujoco --repo-id user/dataset --episodes 10

# Replay a dataset
lerobot-replay --robot.type=lekiwi_mujoco --repo-id user/dataset --episode 0
```

### Programmatic Usage

```python
from lerobot_robot_lekiwi_sim import LeKiwiMujoco, LeKiwiMujocoConfig

config = LeKiwiMujocoConfig()
robot = LeKiwiMujoco(config)
robot.connect()

obs = robot.get_observation()
robot.send_action(obs)  # echo action

robot.disconnect()
```

### Simulation Server Mode (Legacy / ZMQ Host)

For backward compatibility, the ZMQ-based host server is still available.
Install the optional `host` dependencies first:

```bash
uv pip install -e "packages/lekiwi_sim/[host]"
uv run lekiwi_sim_host
```

This creates a server compatible with `lerobot.robots.LeKiwiClient` API.

### Standalone Visualization
For direct MuJoCo simulation without server:

```bash
uv run standalone_mujoco_sim
```

This mode is useful for:
- Model debugging
- Physics parameter tuning
- Visual inspection of robot behavior

> **Note:** With editable installs (`uv pip install -e`), `pkgutil.iter_modules()` doesn't enumerate the package, so `register_third_party_devices()` won't auto-discover it during development. In production installs (non-editable), auto-discovery works automatically. During development, explicitly importing `lerobot_robot_lekiwi_sim` before using the CLI will trigger registration.
