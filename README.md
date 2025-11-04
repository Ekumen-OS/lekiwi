# LeKiwi

[![CI](https://github.com/ekumenlabs/rnd_lekiwi/workflows/ci/badge.svg)](https://github.com/ekumenlabs/rnd_lekiwi/actions)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## :globe_with_meridians: Overview

Comprehensive monorepo for LeKiwi robot software development, combining simulation, control, and machine learning capabilities. This workspace integrates Rust and Python packages to provide a complete robotics development environment supporting both physical and simulated LeKiwi robots.

### Key Features

- **🔄 Simulation Environment**: High-fidelity MuJoCo-based simulation
- **🤖 Real Robot Integration**: Direct control of physical LeKiwi robots
- **🧠 ML Pipeline**: LeRobot integration for learning and inference
- **📡 Dora Integration**: Distributed computing with Dora framework
- **🔧 Development Tools**: Comprehensive tooling for teleoperation and data collection

## :package: Project Structure

```
lekiwi-dora/
├── 📁 packages/                             # Python packages
│   ├── 🎮 lekiwi_sim/                       # MuJoCo simulation environment
│   ├── 🤖 lekiwi_lerobot/                   # LeRobot integration scripts
│   └── 🕹️ lekiwi_teleoperate/               # Teleoperation interface
├── 📁 dora/                                 # Dora Integration
│   └── 📁 graphs/                           # Dora dataflows
│   └── 📁 node_hub/                         # Dora nodes
│       ├── 🔗 dora_lekiwi_client/           # Robot interface node
│       ├── 🧠 dora_run_policy/              # Policy execution node
│       └── 📡 dora_lekiwi_action_publisher/ # Action publisher
├── 📁 crates/                               # Rust packages
└── 📁 .devcontainer/                        # Development environment
```

## :rocket: Quick Start

### Prerequisites

**For Real Robot:**
- [LeKiwi robot hardware](https://github.com/SIGRobotics-UIUC/LeKiwi)
- Ubuntu 22.04 LTS

**For Simulation:**
- Docker with GPU support
- Ubuntu 22.04 LTS (or via devcontainer)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ekumenlabs/rnd_lekiwi.git
   cd lekiwi-dora
   ```

2. **Use devcontainer (Recommended):**
   See [Development Environment Setup](.devcontainer/README.md)

   ```bash
   # Open in VS Code and select "Reopen in Container"
   # OR use devcontainer CLI
   devcontainer up --workspace-folder .
   ```

3. **Manual setup:**
   ```bash
   # Create Python virtual environment
   uv venv -p 3.11 --seed
   source .venv/bin/activate

   # Install packages in development mode
   uv pip install -e .

   # Build Rust packages
   cargo build
   ```

### Running the Simulation

**Terminal 1 - Start simulation:**
```bash
uv run lekiwi_host_sim
```

**Terminal 2 - Teleoperate:**
```bash
uv run lekiwi_teleoperate
```

## :gear: Build System

This monorepo uses multiple build systems:

### Python Packages (UV)
```bash
# Install all packages in development mode
uv pip install -e .

# Build distribution packages
uv build --all-packages

# Run specific package command
uv run lekiwi_sim_standalone
```

### Rust Packages (Cargo)
```bash
# Build all Rust crates
cargo build

# Run tests
cargo test
```

## 🎮 Simulation

The `lekiwi_sim` package provides a high-fidelity MuJoCo simulation environment that serves as a drop-in replacement for the real robot's host server. The implementation replicates LeRobot's `lekiwi_host` server interface, allowing seamless switching between simulation and real hardware without code changes. This means all LeRobot tools and scripts (teleoperation, recording, policy execution) work identically with both the simulated and physical robot.

<img src="docs/media/lekiwi_sim.png" alt="LeKiwi Simulation" width="600">

**Key Features:**
- Physics-accurate omniwheel modeling
- Real-time robot visualization
- Camera feed simulation
- Compatible with LeRobot API

**Two Modes Available:**

1. **Standalone Viewer** (`standalone_mujoco_sim`):
   - Direct MuJoCo visualization only
   - Interactive joint control via GUI
   - Useful for model debugging and physics parameter tuning
   - No server/client architecture required

   ```bash
   uv run standalone_mujoco_sim
   ```

2. **Server Mode** (`lekiwi_host_sim`):
   - Replicates LeRobot's `lekiwi_host` server
   - Enables interaction via `LeKiwiClient` API
   - Compatible with teleoperation, recording, and policy execution
   - Works exactly like the real robot from the client perspective

   ```bash
   uv run lekiwi_host_sim
   ```

See [packages/lekiwi_sim/README.md](packages/lekiwi_sim/README.md) for detailed documentation.

## 🤖 LeRobot Integration

Integration with [LeRobot](https://huggingface.co/docs/lerobot/en/lekiwi) provides machine learning capabilities for the LeKiwi robot, including teleoperation, data collection, and policy training.

**Features:**
- **🕹️ Teleoperation**: Manual robot control via keyboard for demonstrations
- **📹 Data Collection**: Record teleoperation episodes for training
- **🧠 Policy Training**: Train ACT and other imitation learning policies
- **🚀 Policy Deployment**: Run trained models on robot/simulation

### Teleoperation

Manual control interface using the LeRobot API:

```bash
# Start simulation or real robot first
uv run lekiwi_host_sim  # For simulation

# Then teleoperate
uv run lekiwi_teleoperate
```

### Data Collection & Training

```bash
# Record teleoperation demonstrations
uv run lekiwi_lerobot_record --repo-id your_username/dataset_name --episodes 50

# Replay recorded episodes to verify
uv run lekiwi_lerobot_replay --repo-id your_username/dataset_name --episode 0

# Train a policy (see lekiwi_lerobot README for full training options)
python -m lerobot.scripts.train \
  --dataset.repo_id=your_username/dataset_name \
  --policy.type=act \
  --output_dir=outputs/my_policy
```

See [packages/lekiwi_lerobot/README.md](packages/lekiwi_lerobot/README.md) for detailed documentation.

## 📡 Dora Integration

[Dora](https://dora-rs.ai/) enables distributed computing and dataflow orchestration for robotics applications, providing a powerful framework for building modular, distributed robot control systems.

### Dora Nodes

- **dora_lekiwi_client**: Interfaces with robot hardware/simulation, publishes observations and executes actions
- **dora_run_policy**: Executes trained ML policies (ACT, Diffusion, etc.) for action prediction
- **dora_lekiwi_action_publisher**: Publishes hardcoded robot actions for testing and debugging

### Available Dataflows

The repository includes pre-configured dataflow graphs in `dora/lekiwi_sim/graphs/`:

**1. Policy Execution Dataflow** (`mujoco_sim.yml`):
   - Complete pipeline for running trained policies on simulation
   - Connects robot observations → policy inference → robot actions
   - Includes camera feeds and state observations
   - Configurable policy model via environment variables

### Running Dora Dataflows

**Prerequisites:**
```bash
# Start simulation in separate terminal
uv run lekiwi_host_sim
```

**Run the policy execution dataflow:**
```bash
# Navigate to dataflow directory
cd dora/lekiwi_sim/graphs/

# Start the dataflow
dora run mujoco_sim.yml --uv

```

**Optional features** (uncomment in `mujoco_sim.yml`):
- **Visualization**: Enable `rerun-viz` node for real-time 3D visualization
- **Data Recording**: Enable `dora-record` node to save observations to Parquet files
- **Testing Mode**: Use `dora_lekiwi_action_publisher` instead of policy for hardcoded actions

See [Dora documentation](https://dora-rs.ai/docs) for more details on dataflow configuration.

## :test_tube: Testing

```bash
# Run Python tests
uv run pytest

# Run Rust tests
cargo test

# Run pre-commit checks
pre-commit run --all-files
```

## :raised_hands: Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Code Quality

This repository uses:
- **pre-commit hooks** for automated code quality checks
- **GitHub Actions CI** for continuous integration
- **ruff** for Python linting and formatting
- **cargo clippy** for Rust linting

## :books: Documentation

- [Development Environment Setup](.devcontainer/README.md)
- [Simulation Package](packages/lekiwi_sim/README.md)
- [LeRobot Integration](packages/lekiwi_lerobot/README.md)
- [Teleoperation](packages/lekiwi_teleoperate/README.md)
- [LeKiwi Hardware Documentation](https://github.com/SIGRobotics-UIUC/LeKiwi)
- [LeRobot Official Docs](https://huggingface.co/docs/lerobot/en/lekiwi)

## :scroll: License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## :busts_in_silhouette: Acknowledgments

- [SIGRobotics-UIUC](https://github.com/SIGRobotics-UIUC) for the original LeKiwi robot design
- [LeRobot team](https://github.com/huggingface/lerobot) for the robotics learning framework
- [Dora team](https://dora-rs.ai/) for the distributed computing framework
