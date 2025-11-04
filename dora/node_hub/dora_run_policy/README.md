# Dora Policy Runner (dora_run_policy)

Dora node for executing trained machine learning policies on LeKiwi robot observations. This node processes multi-modal sensor data and generates real-time robot actions using pre-trained models from the LeRobot ecosystem.

## Overview

This node serves as the inference engine within Dora dataflows, providing:

- **Multi-modal Processing**: Handles robot state, images, and sensor data
- **Policy Inference**: Runs ACT, Diffusion, and other LeRobot policies
- **Real-time Execution**: Optimized for low-latency robot control
- **Model Management**: Automatic model loading and configuration

## Installation

```bash
# From repository root
uv pip install -e dora/node_hub/dora_run_policy/

# Or with virtual environment
uv venv -p 3.11 --seed
source .venv/bin/activate
uv pip install -e dora/node_hub/dora_run_policy/
```

## Configuration

### Environment Variables

- `POLICY_MODEL`: Model repository or path (default: `francocipollone/act_lekiwi_sim_cubes`)
- `POLICY_TYPE`: Type of pre-trained policy (default: `act`)

## Dora Dataflow Integration

### Inputs
- `tick`: Trigger for policy inference
- `observation_state`: Robot joint states and sensor data
- `image_front`: Front camera
- `image_wrist`: Wrist camera

### Outputs
- `actions`: Predicted robot actions (joint targets)

### YAML Specification

```yaml
nodes:
  - id: dora_run_policy
    build: uv pip install -e ../../node_hub/dora_run_policy
    path: dora_run_policy
    inputs:
      tick: dora/timer/millis/10
      observation_state: dora_lekiwi_client/observation_state
      image_front: dora_lekiwi_client/image_front
      image_wrist: dora_lekiwi_client/image_wrist
    outputs:
      - actions
    env:
      POLICY_TYPE: ACT
      POLICY_MODEL: francocipollone/act_lekiwi_sim_cubes
```

## License

This component is released under the Apache License 2.0, same as the parent repository.
