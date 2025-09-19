# Lekiwi Sim

MuJoCo simulation of Lekiwi robot.

## Getting Started

### Build

 - Install the package: `uv pip install -e .`
  Note: If you don't have a `venv` already in the root workspace then create environment first: `uv venv -p 3.11 --seed`

### Run Simulation

 - Run MuJoCo simulation sever:
   - `uv run lekiwi_sim_host`
     - Once this is running you can use all the `lerobot` machinery with `lekiwi` robot via the `lerobot.robot.LekiwiClient` API.
       - Check [lekiwi_teleoperate](../lekiwi_teleoperate/README.md) and [lekiwi_lerobot](../lekiwi_lerobot/README.md)

 - For running just the standalone MuJoCo simulation: `uv run standalone_mujoco_sim`
