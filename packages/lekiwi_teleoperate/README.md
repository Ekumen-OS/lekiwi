# Lekiwi Teleoperate

Provides keyboard teleoperation for both the base and the arm of the lekiwi.
It works with

## Getting Started

### Build

 - Install the package: `uv pip install -e .`
  Note: If you don't have a `venv` already in the root workspace then create environment first: `uv venv -p 3.11 --seed`

### Teleoperate the Lekiwi

 - Run lekiwi simulation OR real robot
   - Sim (see [lekiwi_sim](../lekiwi_sim/README.md)):
     - `uv run lekiwi_sim_host`
   - Real (see https://huggingface.co/docs/lerobot/en/lekiwi)
     - Summary: SSH into the Lekiwi's Raspberry:
       -  `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
-  Run teleoperation
   -  `uv run lekiwi_teleoperate`
      -  Use `--ip` flag if running the host in a different machine.
