"""Configuration for the LeKiwi keyboard teleoperator plugin."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lerobot.teleoperators.config import TeleoperatorConfig

DEFAULT_BASE_TELEOP_KEYS: dict[str, str] = {
    "forward": "w",
    "backward": "s",
    "left": "a",
    "right": "d",
    "rotate_left": "z",
    "rotate_right": "x",
    "speed_up": "r",
    "speed_down": "f",
}

DEFAULT_ARM_TELEOP_KEYS: dict[str, str] = {
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


@TeleoperatorConfig.register_subclass("lekiwi_keyboard")
@dataclass(kw_only=True)
class LeKiwiKeyboardTeleopConfig(TeleoperatorConfig):
    """Configuration for the LeKiwi keyboard teleoperator.

    This teleoperator provides full keyboard control of the LeKiwi robot
    (omnidirectional base + 5-DoF arm + gripper).

    When ``leader_arm_port`` is set, a physical SO-101 leader arm is used
    for arm control instead of the keyboard.

    Attributes:
        base_teleop_keys: Key bindings for base movement and speed control.
        arm_teleop_keys: Key bindings for arm joint control (ignored when
            a leader arm is configured).
        speed_levels: List of speed presets for base movement, each with
            ``xy`` (m/s) and ``theta`` (deg/s) values.
        initial_speed_index: Index into ``speed_levels`` to start at.
        arm_step_deg: Degrees to increment/decrement arm joints per step
            (ignored when a leader arm is configured).
        leader_arm_port: Serial port of the SO-101 leader arm. When
            ``None`` (default), the arm is controlled via the keyboard.
        leader_arm_id: Device id for the leader arm (used for calibration
            file lookup).
        leader_arm_calibration_dir: Directory holding calibration files
            for the leader arm.

    """

    base_teleop_keys: dict[str, str] = field(default_factory=DEFAULT_BASE_TELEOP_KEYS.copy)
    arm_teleop_keys: dict[str, str] = field(default_factory=DEFAULT_ARM_TELEOP_KEYS.copy)

    speed_levels: list[dict[str, float]] = field(
        default_factory=lambda: [
            {"xy": 0.1, "theta": 30},  # slow
            {"xy": 0.2, "theta": 60},  # medium
            {"xy": 0.3, "theta": 90},  # fast
        ]
    )
    initial_speed_index: int = 0

    arm_step_deg: float = 1.0

    # Leader arm (optional) ------------------------------------------------
    leader_arm_port: str | None = None
    leader_arm_id: str = "lekiwi_leader_arm"
    leader_arm_calibration_dir: Path | None = None
