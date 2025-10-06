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
Example: `uv run lekiwi_lerobot_replay --repo-id francocipollone/lekiwi_sim_cubes --episode 0`


### Training a model

Once you have a dataset you can start training a model. For this, we can rely directly on the lerobot utilities.

```
uv run python -m lerobot.scripts.train \
  --dataset.repo_id=francocipollone/pick_up_cubes \
  --policy.type=act \
  --output_dir=outputs/train/francocipollone/act_lekiwi_sim_cubes \
  --job_name=lerobot_training \
  --policy.device=cuda \
  --policy.repo_id=<your_repo_id>
  --wandb.enable=true
```

### Run the policy

A simple script for running inference with the model is provided.
```
uv run lekiwi_lerobot_run_policy -p <repo_id_or_local_policy_path>
```
Example: `uv run lekiwi_lerobot_run_policy -p francocipollone/act_lekiwi_sim_cubes

### Evaluating a model

Evaluating the model while running the policy. A lerobot-inspired script is added for the evaluation:
```
uv run lekiwi_lerobot_evaluate --repo-id <hf_username/model_name> --policy <hf_username/model_name>
```
Example: `uv run lekiwi_lerobot_evaluate -r francocipollone/eval_act_lekiwi_sim_cubes --policy francocipollone/act_lekiwi_sim_cubes`
