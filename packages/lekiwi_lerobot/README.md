# LeKiwi LeRobot Integration (lekiwi_lerobot)

Machine learning integration package for the LeKiwi robot, providing tools for data collection, policy training, and automated evaluation. This package bridges the gap between manual teleoperation and autonomous behavior through the LeRobot framework.

## Features

- **📹 Data Recording**: Capture high-quality demonstration episodes
- **🔄 Replay System**: Reproduce recorded behaviors accurately
- **🧠 Policy Training**: Train ACT and other imitation learning models
- **📊 Evaluation**: Automated policy assessment and benchmarking
- **☁️ Cloud Integration**: Seamless Hugging Face Hub integration
- **🎯 Multi-Environment**: Works with both real robot and simulation

## Prerequisites

- Python 3.11+
- [lerobot](https://pypi.org/project/lerobot/) >= 0.3.3
- [lekiwi_teleoperate](../lekiwi_teleoperate/) >= 0.1.0
- Hugging Face account with authentication
- CUDA-capable GPU (recommended for training)

## Installation

```bash
# From repository root
uv pip install -e packages/lekiwi_lerobot/

# Or if no virtual environment exists
uv venv -p 3.11 --seed
source .venv/bin/activate
uv pip install -e packages/lekiwi_lerobot/
```

## Authentication

Authenticate with Hugging Face to store and access datasets:

```bash
huggingface-cli login
# or
hf auth login
```

Get your token from: https://huggingface.co/settings/tokens

## Workflow Overview

1. **Record** demonstrations via teleoperation
2. **Train** policies using recorded data
3. **Evaluate** trained policies automatically
4. **Deploy** successful policies for autonomous operation

## Data Recording

Record demonstration episodes during teleoperation:

```bash
uv run lekiwi_lerobot_record --repo-id username/dataset_name --episodes 5 --task "pick and place"

```

## Data Replay

Reproduce recorded episodes to verify data quality:

```bash
# Replay specific episode
uv run lekiwi_lerobot_replay --repo-id username/dataset_name --episode 0
```
Example:
```bash
uv run lekiwi_lerobot_replay --repo-id francocipollone/lekiwi_sim_cubes --episode 0
```


## Policy Training

Once you have a dataset you can start training a model. For this, we can rely directly on the lerobot utilities.
Train imitation learning policies using collected data:

```bash
uv run lerobot-train \
  --dataset.repo_id=<username/my_dataset> \
  --policy.type=act \
  --output_dir=outputs/train/username/my_policy \
  --job_name=act_training \
  --policy.device=cuda \
  --policy.repo_id=<username/my_policy_repo>

```

## Policy Inference

Run trained policies for autonomous operation:

```bash
uv run lekiwi_lerobot_run_policy --policy username/my_trained_policy
```
Example:
```bash
`uv run lekiwi_lerobot_run_policy -p francocipollone/act_lekiwi_sim_cubes
```

## Policy Evaluation

Systematically evaluate policy performance:

```bash
uv run lekiwi_lerobot_evaluate \
  --repo-id username/evaluation_results \
  --policy username/my_trained_policy
```

## License

This package follows the same license as the parent repository. See the root LICENSE file for details.
