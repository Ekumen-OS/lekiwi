from typing import Any

import numpy as np


class ArmTeleop:
    """Class to handle arm teleoperation commands from keyboard inputs.

    Mechanism to catch keyboard inputs are not included in this class.
    This class only provides a method to convert a list of pressed keys to arm action commands.
    """

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
