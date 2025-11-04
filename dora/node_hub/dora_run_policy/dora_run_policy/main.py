"""Dora node for running LeKiwi robot policies.

This module provides a Dora node that processes observations from LeKiwi robot
sensors and runs an ACT policy to predict actions. It handles image processing,
observation frame building, and action prediction in real-time.
"""

import os
from typing import Any, Dict, Tuple

import cv2
import numpy as np
import pyarrow as pa
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.utils.control_utils import predict_action
from lerobot.utils.utils import get_safe_torch_device

from dora import Node  # type: ignore


def convert_bgr_unflatten_image_to_ndarray(
    flat_image: np.ndarray, height: int, width: int, channels: int
) -> np.ndarray:
    """Convert a flat BGR image array to an ndarray with shape (height, width, channels)."""
    image_array = np.array(flat_image, dtype=np.uint8)
    image_array = image_array.reshape((height, width, channels))
    # Convert BGR to RGB
    return cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)


def build_observation_features(
    obs_state_metadata: Dict[str, Any],
    image_front_metadata: Dict[str, Any],
    image_wrist_metadata: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build action and observation features dictionaries from metadata."""
    action_features_list = obs_state_metadata.get("action_features", [])
    action_features = {f: type(float()) for f in action_features_list}

    observation_features_list = obs_state_metadata.get("observation_features", [])
    observation_features: Dict[str, Any] = {
        f: type(float()) for f in observation_features_list
    }

    # Handle image features with proper dimensions
    if "front" in observation_features:
        observation_features["front"] = (
            image_front_metadata.get("height", 480),
            image_front_metadata.get("width", 640),
            3,
        )
    if "wrist" in observation_features:
        observation_features["wrist"] = (
            image_wrist_metadata.get("height", 640),
            image_wrist_metadata.get("width", 480),
            3,
        )

    return action_features, observation_features


def build_observation_dict(
    observation_features: Dict[str, Any],
    obs_state_value: np.ndarray,
    image_front_value: np.ndarray,
    image_wrist_value: np.ndarray,
) -> Dict[str, Any]:
    """Build observation dictionary from raw data."""
    observation = {}
    state_index = 0

    for feature_name, feature_spec in observation_features.items():
        if feature_name == "front":
            observation[feature_name] = convert_bgr_unflatten_image_to_ndarray(
                image_front_value, *feature_spec
            )
        elif feature_name == "wrist":
            observation[feature_name] = convert_bgr_unflatten_image_to_ndarray(
                image_wrist_value, *feature_spec
            )
        else:
            # For non-image features, use state values
            observation[feature_name] = obs_state_value[state_index]
            state_index += 1

    return observation


def main() -> None:
    """Main entry point for the policy runner node.

    This node processes observations from LeKiwi robot sensors and runs an ACT policy
    to predict actions. It waits for tick events and processes the latest observation
    data to generate robot actions.
    """
    node = Node()

    # State variables to store latest events
    last_observation_state_event = None
    last_image_front_event = None
    last_image_wrist_event = None

    # Load policy from environment variable or use default
    policy_type = os.getenv("POLICY_TYPE", "act")
    model_name = os.getenv("POLICY_MODEL", "francocipollone/act_lekiwi_sim_cubes")

    try:
        policy = None
        if policy_type.lower() == "act":
            policy = ACTPolicy.from_pretrained(model_name)
        else:
            raise ValueError(f"Unsupported policy type: {policy_type}")
        policy.reset()
        device_name = policy.config.device or "auto"
        device = get_safe_torch_device(device_name)
    except Exception as e:
        raise RuntimeError(f"Failed to load policy '{model_name}': {e}") from None

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                # Check if we have all required data
                if (
                    last_observation_state_event is None
                    or last_image_front_event is None
                    or last_image_wrist_event is None
                ):
                    continue

                try:
                    # Extract data from events
                    obs_state_metadata = last_observation_state_event["metadata"]
                    obs_state_value = last_observation_state_event["value"].to_numpy()

                    image_front_metadata = last_image_front_event["metadata"]
                    image_front_value = last_image_front_event["value"].to_numpy()

                    image_wrist_metadata = last_image_wrist_event["metadata"]
                    image_wrist_value = last_image_wrist_event["value"].to_numpy()

                    # Build feature specifications
                    action_features, observation_features = build_observation_features(
                        obs_state_metadata, image_front_metadata, image_wrist_metadata
                    )

                    # Build dataset features for LeRobot
                    hw_action_features = hw_to_dataset_features(
                        action_features, "action"
                    )
                    hw_obs_features = hw_to_dataset_features(
                        observation_features, "observation"
                    )
                    dataset_features = {**hw_action_features, **hw_obs_features}

                    # Build observation dictionary
                    observation = build_observation_dict(
                        observation_features,
                        obs_state_value,
                        image_front_value,
                        image_wrist_value,
                    )

                    # Create observation frame for policy
                    observation_frame = build_dataset_frame(
                        dataset_features, observation, prefix="observation"
                    )

                    # Predict action using policy
                    raw_action = predict_action(
                        observation_frame,
                        policy,
                        device,
                        policy.config.use_amp,
                    )

                    # Send action output
                    metadata = event["metadata"].copy()
                    metadata["primitive"] = "series"
                    node.send_output(
                        output_id="actions",
                        data=pa.array(raw_action.tolist()),
                        metadata=metadata,
                    )

                except Exception as e:
                    print(f"Error processing observation: {e}")
                    continue
                finally:
                    # Reset state for next iteration
                    last_observation_state_event = None
                    last_image_front_event = None
                    last_image_wrist_event = None

            elif event["id"] == "observation_state":
                last_observation_state_event = event.copy()
            elif event["id"] == "image_front":
                last_image_front_event = event.copy()
            elif event["id"] == "image_wrist":
                last_image_wrist_event = event.copy()


if __name__ == "__main__":
    main()
