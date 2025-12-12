from typing import Any

import numpy as np


class ArmTeleop:
    """Class to handle arm teleoperation commands from keyboard inputs.

    Mechanism to catch keyboard inputs are not included in this class.
    This class only provides a method to convert a list of pressed keys to arm action commands.
    """

    ARM_TELEOP_KEYS = {
        "shoulder_pan_left": "g",
        "shoulder_pan_right": "t",
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

    JOINT_LIMITS = {
        "shoulder_pan": (-110.0, 110.0),  # 1.92 rad
        "shoulder_lift": (-100.0, 100.0),  # 1.75 rad
        "elbow_flex": (-95.0, 95.0),  # 1.66 rad
        "wrist_flex": (-95.0, 95.0),  # 1.66 rad
        "wrist_roll": (-160.0, 160.0),  # 2.79 rad
        "gripper": (0.0, 34.4),  # 0.6 rad
    }

    def __init__(self) -> None:
        """Initialize the ArmTeleop class with default joint commands."""
        self.shoulder_pan_cmd = 0.0  # deg
        self.shoulder_lift_cmd = 0.0  # deg
        self.elbow_flex_cmd = 0.0  # deg
        self.wrist_flex_cmd = 0.0  # deg
        self.wrist_roll_cmd = 0.0  # deg
        self.gripper_cmd = 0.0  # deg

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
            self.gripper_cmd += 1.0
        if self.ARM_TELEOP_KEYS["gripper_close"] in pressed_keys:
            self.gripper_cmd -= 1.0
        self._verify_limits()
        return {
            "arm_shoulder_pan.pos": self.shoulder_pan_cmd,
            "arm_shoulder_lift.pos": self.shoulder_lift_cmd,
            "arm_elbow_flex.pos": self.elbow_flex_cmd,
            "arm_wrist_flex.pos": self.wrist_flex_cmd,
            "arm_wrist_roll.pos": self.wrist_roll_cmd,
            "arm_gripper.pos": self.gripper_cmd,
        }

    def _verify_limits(self) -> None:
        """Verify that the joint commands are within the defined limits."""
        self.shoulder_pan_cmd = np.clip(
            self.shoulder_pan_cmd, self.JOINT_LIMITS["shoulder_pan"][0], self.JOINT_LIMITS["shoulder_pan"][1]
        )
        self.shoulder_lift_cmd = np.clip(
            self.shoulder_lift_cmd, self.JOINT_LIMITS["shoulder_lift"][0], self.JOINT_LIMITS["shoulder_lift"][1]
        )
        self.elbow_flex_cmd = np.clip(
            self.elbow_flex_cmd, self.JOINT_LIMITS["elbow_flex"][0], self.JOINT_LIMITS["elbow_flex"][1]
        )
        self.wrist_flex_cmd = np.clip(
            self.wrist_flex_cmd, self.JOINT_LIMITS["wrist_flex"][0], self.JOINT_LIMITS["wrist_flex"][1]
        )
        self.wrist_roll_cmd = np.clip(
            self.wrist_roll_cmd, self.JOINT_LIMITS["wrist_roll"][0], self.JOINT_LIMITS["wrist_roll"][1]
        )
        self.gripper_cmd = np.clip(self.gripper_cmd, self.JOINT_LIMITS["gripper"][0], self.JOINT_LIMITS["gripper"][1])
