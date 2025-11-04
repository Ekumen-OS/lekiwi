"""Dora node for interfacing with the LeKiwi robot.

This module provides a Dora node that connects to a LeKiwi robot and handles
bidirectional communication for observations and actions.
"""

import os
from typing import Any

import numpy as np
import pyarrow as pa
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig

from dora import Node  # type: ignore


def convert_rgb_to_bgr(frame_rgb: np.ndarray) -> np.ndarray:
    """Convert an RGB frame to BGR format.

    This is useful for compatibility with OpenCV and other libraries that expect BGR format.

    Args:
        frame_rgb (numpy.ndarray): Input frame in RGB format (H, W, 3).

    Returns:
        numpy.ndarray: Frame converted to BGR format (H, W, 3).

    """
    CHANNEL_DIMENSION = 3
    if frame_rgb.ndim == CHANNEL_DIMENSION and frame_rgb.shape[2] == CHANNEL_DIMENSION:
        return frame_rgb[:, :, ::-1]
    raise ValueError("Input frame must be a 3-channel RGB image.")


def send_image_output(
    node: Node, output_id: str, image: np.ndarray, base_metadata: Any
) -> None:
    """Send image data as Dora output with proper metadata.

    Args:
        node: The Dora node instance
        output_id: The output identifier for this image
        image: RGB image array to send
        base_metadata: Base metadata to extend with image-specific fields

    """
    frame = convert_rgb_to_bgr(frame_rgb=image)
    metadata = base_metadata.copy()
    metadata.update(
        {
            "encoding": "bgr8",
            "primitive": "image",  # Used by other nodes like dora-rerun
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
        }
    )

    # Send the camera image as a flattened array
    node.send_output(
        output_id, data=pa.array(frame.ravel(), type=pa.uint8()), metadata=metadata
    )


def initialize_robot_client() -> LeKiwiClient:
    """Initialize and connect to the LeKiwi robot.

    Returns:
        LeKiwiClient: Connected robot client

    Raises:
        ValueError: If LEKIWI_IP environment variable is not set
        ConnectionError: If robot connection fails

    """
    lekiwi_ip = os.getenv("LEKIWI_IP", "127.0.0.1")
    if not lekiwi_ip:
        raise ValueError("LEKIWI_IP environment variable is not set.")

    robot_config = LeKiwiClientConfig(remote_ip=lekiwi_ip, id="my_lekiwi")
    robot = LeKiwiClient(robot_config)
    robot.connect()

    if not robot.is_connected:
        raise ConnectionError("Robot is not connected!")

    return robot


def main() -> None:
    """Main entry point for the node.

    This Node interfaces with the Lekiwi via the LekiwiClient.

    INPUTS
    - tick: A tick event that triggers the node's processing.
    - actions: A list of actions to be sent to the Lekiwi.

    OUTPUTS
    - observations: A list of observations returned by the Lekiwi.

    """
    node = Node()
    robot = initialize_robot_client()
    action_features = list(robot.action_features.keys())
    observation_features = list(robot.observation_features.keys())
    print("action features:", robot.action_features)
    print("observation features:", robot.observation_features)

    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "tick":
                # Handle tick event
                observation = robot.get_observation()
                observation_state = observation["observation.state"]

                # Send observation state
                state_metadata = event["metadata"].copy()
                state_metadata["primitive"] = (
                    "series"  # Used by other nodes like dora-rerun
                )
                state_metadata["action_features"] = action_features
                state_metadata["observation_features"] = observation_features
                node.send_output(
                    output_id="observation_state",
                    data=pa.array(observation_state),
                    metadata=state_metadata,
                )
                # Send camera images
                send_image_output(
                    node, "image_front", observation["front"], event["metadata"]
                )
                send_image_output(
                    node, "image_wrist", observation["wrist"], event["metadata"]
                )

            elif event["id"] == "actions":
                # Handle actions sent to the robot
                action_data = event["value"].to_numpy()
                # Action data is expected to be sorted in the correct order
                action = {
                    key: action_data[i] for i, key in enumerate(robot.action_features)
                }
                robot.send_action(action)


if __name__ == "__main__":
    main()
