"""TODO: Add docstring."""

import cv2
import pyarrow as pa
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.utils.control_utils import predict_action
from lerobot.utils.utils import get_safe_torch_device

from dora import Node


def convert_bgr_unflatten_image_to_ndarray(flat_image, height, width, channels):
    """Convert a flat BGR image array to an ndarray with shape (height, width, channels)."""
    import numpy as np

    # print("Converting flat image to ndarray with shape:", (height, width, channels))
    image_array = np.array(flat_image, dtype=np.uint8)
    image_array = image_array.reshape((height, width, channels))
    # Convert BGR to RGB
    return cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)


def main():
    """TODO: Add docstring."""
    node = Node()

    last_observation_state_event = None
    last_image_front_event = None
    last_image_wrist_event = None

    policy = ACTPolicy.from_pretrained("francocipollone/act_lekiwi_sim_cubes")
    policy.reset()
    device = get_safe_torch_device(policy.config.device)

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                if (
                    last_observation_state_event is None
                    or last_image_front_event is None
                    or last_image_wrist_event is None
                ):
                    continue
                # Process observation state
                obs_state_metadata = last_observation_state_event["metadata"]
                obs_state_value = last_observation_state_event["value"].to_numpy()
                # Process image front
                image_front_metadata = last_image_front_event["metadata"]
                image_front_value = last_image_front_event["value"].to_numpy()
                # TODO: Convert from flat array to image format
                # Process image wrist
                image_wrist_metadata = last_image_wrist_event["metadata"]
                image_wrist_value = last_image_wrist_event["value"].to_numpy()
                # TODO: Convert from flat array to image format

                # Compose dataset features based on metadata info.
                action_features_list = obs_state_metadata.get("action_features", [])
                action_features: dict[str, type | tuple] = {
                    f: type(float()) for f in action_features_list
                }
                observation_features_list = obs_state_metadata.get(
                    "observation_features", []
                )
                observation_features: dict[str, type | tuple] = {
                    f: type(float()) for f in observation_features_list
                }
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

                hw_action_features = hw_to_dataset_features(action_features, "action")
                hw_obs_features = hw_to_dataset_features(
                    observation_features, "observation"
                )
                dataset_features = {**hw_action_features, **hw_obs_features}

                # Compose the observation frame
                # I need the observation to be a dict with all features: name and value
                observation = {}
                for i, f in enumerate(observation_features):
                    if f == "front":
                        observation[f] = convert_bgr_unflatten_image_to_ndarray(
                            image_front_value, *observation_features[f]
                        )
                        continue
                    if f == "wrist":
                        observation[f] = convert_bgr_unflatten_image_to_ndarray(
                            image_wrist_value, *observation_features[f]
                        )
                        continue
                    observation[f] = obs_state_value[i]
                observation_frame = build_dataset_frame(
                    dataset_features, observation, prefix="observation"
                )
                # Predict action
                raw_action = predict_action(
                    observation_frame,
                    policy,
                    device,
                    policy.config.use_amp,
                )
                {key: raw_action[i].item() for i, key in enumerate(action_features)}

                # Send action output
                metadata = event["metadata"]
                metadata["primitive"] = "series"
                node.send_output(
                    output_id="actions",
                    data=pa.array(raw_action.tolist()),
                    metadata=metadata,
                )

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
