# Dora LeKiwi Action Publisher (dora_lekiwi_action_publisher)

A simple Dora node for debugging and testing that publishes a hardcoded action array. Useful for testing robot control pipelines without running a full policy.

## Purpose

This node sends a fixed action command repeatedly, allowing you to:
- Test robot control without a trained policy
- Debug dataflow connections
- Verify action processing pipelines
- Quickly prototype control sequences

## Configuration

### Environment Variable

- `LEKIWI_ACTION`: Hardcoded action array (default: `[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]`)

Set a custom action:
```bash
export LEKIWI_ACTION="[0.1, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 1.0]"
```

## Dataflow Integration

### Inputs
- `tick`: Trigger signal (from timer node)

### Outputs
- `actions`: Hardcoded action array as PyArrow array

### Example YAML

```yaml
nodes:
  - id: dora_lekiwi_action_publisher
    build: uv pip install -e dora_lekiwi_action_publisher
    path: dora_lekiwi_action_publisher
    inputs:
      tick: dora/timer/millis/50
    outputs:
      - actions
    env:
      LEKIWI_ACTION: "[0.0, -90, 90, 0.0, 0.0, 0.05, 0.0, 0.0, 0.0]"
```

## Usage

```bash
# Run the dataflow
dora run your_test_dataflow.yml --uv
```

## Related Nodes

- [dora_run_policy](../dora_run_policy/): For running actual ML policies
- [dora_lekiwi_client](../dora_lekiwi_client/): Robot command execution
