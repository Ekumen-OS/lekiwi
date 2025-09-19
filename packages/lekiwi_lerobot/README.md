# lekiwi_lerobot

`lekiwi_lerobot` provides tools for recording and replaying teleoperation episodes with the LeKiwi robot, supporting both real and simulated environments. It integrates with the [`lerobot`](https://huggingface.co/docs/lerobot/en/lekiwi) stack and stores datasets on Hugging Face Hub.

## Features

- **Record**: Capture robot actions and observations during teleoperation or policy execution.
- **Replay**: Play back recorded episodes on a connected LeKiwi robot or simulator.
- **Evaluate**: TODO

## Authentication

Before recording or replaying datasets, authenticate with Hugging Face:

```sh
hf auth login <your_token>
```

## Getting Started

### Build

 - Install the package: `uv pip install -e .`
  Note: If you don't have a `venv` already in the root workspace then create environment first: `uv venv -p 3.11 --seed`

### Recording a dataset

Run the recording client to capture episodes and push them to Hugging Face:

```
uv run lekiwi_lerobot_record --repo-id <hf_username/dataset_name> --episodes <num> --task "<task description>"
```

### Replying a dataset

Run the replay client to play back a recorded episode:

```
uv run lekiwi_lerobot_replay --repo-id <hf_username/dataset_name> --episode <index>
```
Example: `uv run lekiwi_lerobot_replay --repo-id francocipollone/lekiwi_test --episode 0`
