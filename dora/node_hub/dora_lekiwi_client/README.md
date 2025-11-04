# Dora LeKiwi Client (dora_lekiwi_client)

Dora node that interfaces with the LeKiwi robot hardware or simulation, handling bidirectional communication for observations and actions within Dora dataflows.

## Overview

This node serves as the bridge between the LeKiwi robot (real or simulated) and the Dora ecosystem, providing:

- **Observation Publishing**: Streams robot state, camera feeds, and sensor data
- **Action Consumption**: Receives and executes robot commands
- **Data Format Conversion**: Transforms between LeRobot and Dora data formats
- **Connection Management**: Handles robot connectivity and error recovery

## Features

- **📡 Real-time Data Streaming**: Low-latency observation and action handling
- **🤖 Dual Mode Support**: Works with physical robot and simulation
- **📹 Multi-camera Support**: Front and wrist camera feeds
- **🔄 Automatic Reconnection**: Robust connection handling
- **🔧 Configurable**: Environment-based configuration

## Installation

```bash
# From repository root
uv pip install -e dora/node_hub/dora_lekiwi_client/

# Or with virtual environment
uv venv -p 3.11 --seed
source .venv/bin/activate
uv pip install -e dora/node_hub/dora_lekiwi_client/
```

## Configuration

### Environment Variables

- `LEKIWI_IP`: Robot IP address (default: `127.0.0.1`)

### Example Configuration
```bash
export LEKIWI_IP="192.168.1.100"    # Real robot IP
```

## Dora Dataflow Integration

### Inputs
- `tick`: Trigger for observation collection
- `actions`: Robot actions to execute (from policy nodes)

### Outputs
- `observation_state`: Robot joint states and sensor readings
- `image_front`: Front camera RGB feed (BGR format)
- `image_wrist`: Wrist camera RGB feed (BGR format)

### YAML Specification

```yaml
nodes:
  - id: dora_lekiwi_client
    build: uv pip install -e dora/node_hub/dora_lekiwi_client
    path: dora_lekiwi_client
    inputs:
      tick: dora/timer/millis/10
      actions: policy_node/actions
    outputs:
      - observation_state
      - image_front
      - image_wrist
```

## Data Formats

### Observation State
- **Type**: PyArrow Array (float64)
- **Content**: Joint positions, velocities, gripper state
  - `["arm_shoulder_pan.pos", "arm_shoulder_lift.pos", "arm_elbow_flex.pos", "arm_wrist_flex.pos", "arm_wrist_roll.pos", "arm_gripper.pos", "x.vel", "y.vel", "theta.vel"]`
- **Metadata**: Feature names, action features, observation features

### Camera Images
- **Type**: PyArrow Array (uint8)
- **Format**: Flattened BGR image
- **Metadata**: Width, height, encoding, primitive type

### Actions
- **Type**: PyArrow Array (float64)
- **Content**: Target joint positions/velocities
- **Order**: Matches robot.action_features

## Usage Examples

### Basic Dataflow
```yaml
# minimal_dataflow.yml
nodes:
  - id: timer
    operator:
      python: dora-timer
      outputs:
        - tick

  - id: lekiwi_client
    operator:
      python: dora/node_hub/dora_lekiwi_client/dora_lekiwi_client/main.py
    inputs:
      tick: timer/tick
    outputs:
      - observation_state
      - image_front
      - image_wrist
```

## License

This component is released under the Apache License 2.0, same as the parent repository.
