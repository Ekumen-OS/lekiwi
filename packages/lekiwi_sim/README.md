# LeKiwi Simulation (lekiwi_sim)

High-fidelity MuJoCo-based simulation environment for the LeKiwi robot. This package provides a drop-in replacement for the real robot's host server, enabling seamless development and testing using the LeRobot API.

## Features

- **🎯 Physics-Accurate Simulation**: High-fidelity MuJoCo physics engine
- **🤖 Complete Robot Model**: Omniwheel base, robotic arm, and gripper
- **📹 Camera Simulation**: Front and wrist camera feeds
- **🔌 LeRobot Compatible**: Drop-in replacement for real robot
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

### Simulation Server Mode
Start the simulation server that mimics the real robot's host server:

```bash
uv run lekiwi_sim_host
```

This creates a server compatible with `lerobot.robots.LeKiwiClient` API. You can then:
- Use teleoperation: `uv run lekiwi_teleoperate`
- Record episodes: `uv run lekiwi_lerobot_record`
- Run policies: `uv run lekiwi_lerobot_replay`

### Standalone Visualization
For direct MuJoCo simulation without server:

```bash
uv run lekiwi_sim_standalone
```

This mode is useful for:
- Model debugging
- Physics parameter tuning
- Visual inspection of robot behavior

## API Compatibility

The simulation server provides the same API as the real LeKiwi robot so LeKiwiClient implementation from LeRobot can still be used.

```python
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig

# Connect to simulation (default: localhost:5556)
config = LeKiwiClientConfig(remote_ip="127.0.0.1")
robot = LeKiwiClient(config)
robot.connect()

# Get observations
obs = robot.get_observation()
print(obs.keys())  # ['observation.state', 'front', 'wrist']

# Send actions
action = {
    'base.x': 0.1,
    'base.y': 0.0,
    'base.theta': 0.0,
    'arm.joint_1': 0.0,
    # ... other joints
}
robot.send_action(action)
```
