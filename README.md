# lekiwi

## :globe_with_meridians: Description

Monorepo for Lekiwi robot software and tooling. This workspace combines Rust and Python packages to provide:
 - Simulation for LeKiwi robot.
 - LeRobot scripts to be used in both simulated and real robot.
 - Dora integration (TODO)
 - Robotic stack (TODO)

## Prerequisites

 - For real robot:
   - [LeKiwi](https://github.com/SIGRobotics-UIUC/LeKiwi) robot
 - For simulation:
   - Docker (See [#code-development](#code-development))

## Platforms

 - OS:
   - Ubuntu 22.04 Jammy Jellyfish

## :package: Project structure

TODO

## :pick: Workspace setup

Refer to [.devcontainer/README.md](.devcontainer/README.md)

## :gear: Build

### Build systems

This repository combines both `rust` and `python` packages. `cargo` and `uv` are the tools of choice.

#### Rust packages

 - Building `rust` packages:
    ```
    cargo build
    ```

#### Python packages
 - Setup a `venv` within `andino-rs` folder.
    ```
    uv venv -p 3.11 --seed
    ```

 - Building `python` packages:
    ```
    uv build --all-packages
    ```

## Real Robot

Refer to https://huggingface.co/docs/lerobot/en/lekiwi for information about using LeKiwi robot


## Simulation

[lekiwi-sim](packages/lekiwi_sim/) package provides a MuJoCo simulation.
It works as replacement of the `lerobot`'s lekiwi host server that is used with the real robot, allowing the user to continue using `lerobot` API with the simulated environment

<img src="docs/media/lekiwi_sim.png">

### Quick Start

```
uv pip install -e .
```
On terminal #1:
```
uv run lekiwi_host_sim
```
On terminal #2:
```
uv run lekiwi_teleoperate
```
Use the second terminal to teleoperate the robot.

Refer to [lekiwi-sim](packages/lekiwi_sim/README.md) for further information

## *`lerobot`* Integration

Naturally we rely on [lerobot](https://huggingface.co/docs/lerobot/en/lekiwi) machinery for controlling the Lekiwi robot as it contains all the functionalities to control and to integrate it with other ML workflows.
The [`lekiwi_lerobot`](packages/lekiwi_lerobot/README.md) package contains some scripts and tooling for using lerobot API with real and simulated robot.

## *`dora`* Integration

What is dora? See https://dora-rs.ai/

TODO


### Appendix

## :raised_hands: Contributing

Issues or PRs are always welcome! Please refer to [CONTRIBUTING](CONTRIBUTING.md) doc.

## Code development

 - Workspace setup: Refer to [.devcontainer/README.md](.devcontainer/README.md)
 - This repository uses `pre-commit`.
    - To add it to git's hook, use:
     ```
     pip install pre-commit
     pre-commit install
     ```
    - Every time a commit is attempted, pre-commit will run. The checks can be by-passed by adding `--no-verify` to *git commit*, but take into account pre-commit also runs as a required Github Actions check, so you will need it to pass.
