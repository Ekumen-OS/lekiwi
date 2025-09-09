import argparse
import logging
import time
from typing import Any

import numpy as np
from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import _init_rerun, log_rerun_data

FPS = 30

COMMANDS_STR = """
Teleop commands:
Base move:
           {forward}
    {left} {backward} {right}

Rotate:
    clockwise: {rotate_right}
    counter-clockwise: {rotate_left}

Speed:
    up: {speed_up}
    down: {speed_down}

Arm joint position:
    shoulder_pan_left: {shoulder_pan_left}
    shoulder_pan_right: {shoulder_pan_right}
    shoulder_lift_up: {shoulder_lift_up}
    shoulder_lift_down: {shoulder_lift_down}
    elbow_flex_up: {elbow_flex_up}
    elbow_flex_down: {elbow_flex_down}
    wrist_flex_up: {wrist_flex_up}
    wrist_flex_down: {wrist_flex_down}
    wrist_roll_left: {wrist_roll_left}
    wrist_roll_right: {wrist_roll_right}
    gripper_open: {gripper_open}
    gripper_close: {gripper_close}
"""


class ArmTeleop:
    """Class to handle arm teleoperation commands from keyboard inputs."""

    ARM_TELEOP_KEYS = {
        "shoulder_pan_left": "t",
        "shoulder_pan_right": "g",
        "shoulder_lift_up": "y",
        "shoulder_lift_down": "h",
        "elbow_flex_up": "u",
        "elbow_flex_down": "j",
        "wrist_flex_up": "i",
        "wrist_flex_down": "k",
        "wrist_roll_left": "o",
        "wrist_roll_right": "l",
        "gripper_open": "p",
        "gripper_close": ";",
    }

    def __init__(self) -> None:
        """Initialize the ArmTeleop class with default joint commands."""
        self.shoulder_pan_cmd = 0.0  # deg
        self.shoulder_lift_cmd = 0.0  # deg
        self.elbow_flex_cmd = 0.0  # deg
        self.wrist_flex_cmd = 0.0  # deg
        self.wrist_roll_cmd = 0.0  # deg
        self.gripper_cmd = 0.0  # 0.0 to 1

    def from_keyboard_to_arm_action(self, pressed_keys: np.ndarray) -> dict[str, Any]:
        """Convert keyboard inputs to arm action commands.

        Args: pressed_keys (list): List of currently pressed keys.
        Returns: dict: Dictionary with arm action commands.
        """
        if self.ARM_TELEOP_KEYS["shoulder_pan_left"] in pressed_keys:
            self.shoulder_pan_cmd += 1.0
        if self.ARM_TELEOP_KEYS["shoulder_pan_right"] in pressed_keys:
            self.shoulder_pan_cmd -= 1.0
        if self.ARM_TELEOP_KEYS["shoulder_lift_up"] in pressed_keys:
            self.shoulder_lift_cmd += 1.0
        if self.ARM_TELEOP_KEYS["shoulder_lift_down"] in pressed_keys:
            self.shoulder_lift_cmd -= 1.0
        if self.ARM_TELEOP_KEYS["elbow_flex_up"] in pressed_keys:
            self.elbow_flex_cmd += 1.0
        if self.ARM_TELEOP_KEYS["elbow_flex_down"] in pressed_keys:
            self.elbow_flex_cmd -= 1.0
        if self.ARM_TELEOP_KEYS["wrist_flex_up"] in pressed_keys:
            self.wrist_flex_cmd += 1.0
        if self.ARM_TELEOP_KEYS["wrist_flex_down"] in pressed_keys:
            self.wrist_flex_cmd -= 1.0
        if self.ARM_TELEOP_KEYS["wrist_roll_left"] in pressed_keys:
            self.wrist_roll_cmd += 1.0
        if self.ARM_TELEOP_KEYS["wrist_roll_right"] in pressed_keys:
            self.wrist_roll_cmd -= 1.0
        if self.ARM_TELEOP_KEYS["gripper_open"] in pressed_keys:
            self.gripper_cmd += 0.1
        if self.ARM_TELEOP_KEYS["gripper_close"] in pressed_keys:
            self.gripper_cmd -= 0.1

        return {
            "arm_shoulder_pan.pos": self.shoulder_pan_cmd,
            "arm_shoulder_lift.pos": self.shoulder_lift_cmd,
            "arm_elbow_flex.pos": self.elbow_flex_cmd,
            "arm_wrist_flex.pos": self.wrist_flex_cmd,
            "arm_wrist_roll.pos": self.wrist_roll_cmd,
            "arm_gripper.pos": self.gripper_cmd,
        }


# TODO(arilow): Add teleoperation of the arm.
def main() -> None:
    """Main function to run the LeKiwi teleoperation client."""
    parser = argparse.ArgumentParser(description="Run the LeKiwi teleoperation client.")

    parser.add_argument(
        "-l",
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO). Case-insensitive.",
    )
    args = parser.parse_args()
    log_level = args.level.upper()
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info("Configuring LeKiwi teleoperation client")

    # Create the robot and teleoperator configurations
    robot_config = LeKiwiClientConfig(remote_ip="127.0.0.1", id="my_lekiwi")
    keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

    robot = LeKiwiClient(robot_config)
    keyboard = KeyboardTeleop(keyboard_config)

    # To connect you already should have this script running on LeKiwi: `uv run lekiwi_sim`
    robot.connect()
    keyboard.connect()

    _init_rerun(session_name="lekiwi_teleop")

    if not robot.is_connected or not keyboard.is_connected:
        raise ValueError("Robot, leader arm of keyboard is not connected!")

    logging.info("Robot and keyboard are connected.")
    print(COMMANDS_STR.format(**robot_config.teleop_keys, **ArmTeleop.ARM_TELEOP_KEYS))

    arm_teleop = ArmTeleop()

    while True:
        t0 = time.perf_counter()

        observation = robot.get_observation()

        keyboard_keys = keyboard.get_action()
        base_action = robot._from_keyboard_to_base_action(keyboard_keys)
        arm_action = arm_teleop.from_keyboard_to_arm_action(keyboard_keys)

        log_rerun_data(observation, {**arm_action, **base_action})

        action = {**base_action, **arm_action}  # Merge base and arm actions
        logging.debug("Sending action: %s", action)
        robot.send_action(action)

        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
