"""LeRobot Teleoperator plugin: full keyboard teleoperation for the LeKiwi robot."""

import logging
import os
import sys
from functools import cached_property
from typing import Any

import numpy as np
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from lerobot.teleoperators.teleoperator import Teleoperator
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from .config_lekiwi_keyboard import LeKiwiKeyboardTeleopConfig

PYNPUT_AVAILABLE = True
try:
    if ("DISPLAY" not in os.environ) and ("linux" in sys.platform):
        logging.info("No DISPLAY set. Skipping pynput import.")
        raise ImportError("pynput blocked intentionally due to no display.")

    from pynput import keyboard
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False
except Exception as e:
    keyboard = None
    PYNPUT_AVAILABLE = False
    logging.info(f"Could not import pynput: {e}")


# Joint limits in degrees for the LeKiwi arm.
JOINT_LIMITS: dict[str, tuple[float, float]] = {
    "shoulder_pan": (-110.0, 110.0),
    "shoulder_lift": (-100.0, 100.0),
    "elbow_flex": (-95.0, 95.0),
    "wrist_flex": (-95.0, 95.0),
    "wrist_roll": (-160.0, 160.0),
    "gripper": (0.0, 34.4),
}

logger = logging.getLogger(__name__)


class LeKiwiKeyboardTeleop(Teleoperator):
    """Full-keyboard teleoperator for the LeKiwi robot.

    Combines omnidirectional base control (WASD + ZX for rotation, R/F for speed)
    and arm joint control into a single LeRobot ``Teleoperator`` plugin.

    When a ``leader_arm_port`` is specified in the config, arm actions are read
    from a physical SO-101 leader arm instead of the keyboard.  The keyboard is
    always used for base movement.

    The action dict returned by :pymeth:`get_action` matches the ``action_features``
    of the ``LeKiwiMujoco`` / ``LeKiwi`` robots, so this teleoperator can be used
    directly with ``lerobot-teleoperate --teleop.type=lekiwi_keyboard``.
    """

    config_class = LeKiwiKeyboardTeleopConfig
    name = "lekiwi_keyboard"

    def __init__(self, config: LeKiwiKeyboardTeleopConfig) -> None:
        """Initialize the LeKiwi keyboard teleoperator."""
        super().__init__(config)
        self.config = config

        # Keyboard listener state
        self._current_pressed: dict[str, bool] = {}
        self._listener = None

        # Base speed state
        self._speed_index = config.initial_speed_index

        # Arm joint state (accumulated positions in degrees, keyboard mode only)
        self._arm_state: dict[str, float] = {
            "arm_shoulder_pan.pos": 0.0,
            "arm_shoulder_lift.pos": 0.0,
            "arm_elbow_flex.pos": 0.0,
            "arm_wrist_flex.pos": 0.0,
            "arm_wrist_roll.pos": 0.0,
            "arm_gripper.pos": 0.0,
        }

        # Optional leader arm (created lazily in connect())
        self._leader_arm: Teleoperator | None = None

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    @cached_property
    def action_features(self) -> dict[str, type]:
        """Action dict keys matching LeKiwi's action space (6 arm joints + 3 base velocities)."""
        return dict.fromkeys(
            (
                "arm_shoulder_pan.pos",
                "arm_shoulder_lift.pos",
                "arm_elbow_flex.pos",
                "arm_wrist_flex.pos",
                "arm_wrist_roll.pos",
                "arm_gripper.pos",
                "x.vel",
                "y.vel",
                "theta.vel",
            ),
            float,
        )

    @cached_property
    def feedback_features(self) -> dict:
        """No feedback is sent back to this teleoperator."""
        return {}

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return whether the keyboard listener is active.

        When a leader arm is configured, both the keyboard listener and the
        leader arm must be connected.
        """
        keyboard_ok = PYNPUT_AVAILABLE and self._listener is not None and self._listener.is_alive()
        if self._leader_arm is not None:
            return keyboard_ok and self._leader_arm.is_connected
        return keyboard_ok

    def connect(self, calibrate: bool = True) -> None:
        """Start the keyboard listener and, optionally, the leader arm.

        Parameters
        ----------
        calibrate : bool
            Passed through to the leader arm's ``connect()`` when one is
            configured.  Unused for the keyboard listener itself.

        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} is already connected.")

        if not PYNPUT_AVAILABLE:
            raise DeviceNotConnectedError("pynput is not available (no DISPLAY?). Cannot start keyboard listener.")

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

        # Connect leader arm when configured
        if self.config.leader_arm_port is not None:
            leader_cfg = SO101LeaderConfig(
                port=self.config.leader_arm_port,
                id=self.config.leader_arm_id,
                calibration_dir=self.config.leader_arm_calibration_dir,
            )
            self._leader_arm = SO101Leader(leader_cfg)
            self._leader_arm.connect(calibrate=calibrate)
            logger.info("Leader arm connected on %s.", self.config.leader_arm_port)

        logger.info("%s connected.", self)

    @property
    def is_calibrated(self) -> bool:
        """Return True when no leader arm is attached, otherwise delegate."""
        if self._leader_arm is not None:
            return self._leader_arm.is_calibrated
        return True

    def calibrate(self) -> None:
        """Forward calibration to the leader arm if one is connected."""
        if self._leader_arm is not None:
            self._leader_arm.calibrate()

    def configure(self) -> None:
        """No-op for keyboard teleoperator."""

    # ------------------------------------------------------------------
    # Keyboard callbacks
    # ------------------------------------------------------------------

    def _on_press(self, key) -> None:
        if hasattr(key, "char") and key.char is not None:
            self._current_pressed[key.char] = True

    def _on_release(self, key) -> None:
        if hasattr(key, "char") and key.char is not None:
            self._current_pressed[key.char] = False

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def get_action(self) -> dict[str, Any]:
        """Read currently pressed keys and produce a full LeKiwi action dict.

        Returns:
            dict with 6 arm joint positions (degrees) and 3 base velocities.

        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected. Call connect() first.")

        pressed = {k for k, v in self._current_pressed.items() if v}

        # --- Base ---
        base_action = self._compute_base_action(pressed)

        # --- Arm ---
        if self._leader_arm is not None:
            arm_action = self._leader_arm.get_action()
            # SO101Leader returns keys like "shoulder_pan.pos"; prefix with "arm_"
            arm_action = {f"arm_{k}": v for k, v in arm_action.items()}
        else:
            arm_action = self._compute_arm_action(pressed)

        return {**arm_action, **base_action}

    def _compute_base_action(self, pressed: set[str]) -> dict[str, float]:
        keys = self.config.base_teleop_keys

        # Speed control
        if keys["speed_up"] in pressed:
            self._speed_index = min(self._speed_index + 1, len(self.config.speed_levels) - 1)
        if keys["speed_down"] in pressed:
            self._speed_index = max(self._speed_index - 1, 0)

        speed = self.config.speed_levels[self._speed_index]
        xy_speed = speed["xy"]
        theta_speed = speed["theta"]

        x_cmd = 0.0
        y_cmd = 0.0
        theta_cmd = 0.0

        if keys["forward"] in pressed:
            x_cmd += xy_speed
        if keys["backward"] in pressed:
            x_cmd -= xy_speed
        if keys["left"] in pressed:
            y_cmd += xy_speed
        if keys["right"] in pressed:
            y_cmd -= xy_speed
        if keys["rotate_left"] in pressed:
            theta_cmd += theta_speed
        if keys["rotate_right"] in pressed:
            theta_cmd -= theta_speed

        return {
            "x.vel": x_cmd,
            "y.vel": y_cmd,
            "theta.vel": theta_cmd,
        }

    def _compute_arm_action(self, pressed: set[str]) -> dict[str, float]:
        keys = self.config.arm_teleop_keys
        step = self.config.arm_step_deg

        # Accumulate increments
        if keys["shoulder_pan_left"] in pressed:
            self._arm_state["arm_shoulder_pan.pos"] += step
        if keys["shoulder_pan_right"] in pressed:
            self._arm_state["arm_shoulder_pan.pos"] -= step

        if keys["shoulder_lift_up"] in pressed:
            self._arm_state["arm_shoulder_lift.pos"] += step
        if keys["shoulder_lift_down"] in pressed:
            self._arm_state["arm_shoulder_lift.pos"] -= step

        if keys["elbow_flex_up"] in pressed:
            self._arm_state["arm_elbow_flex.pos"] += step
        if keys["elbow_flex_down"] in pressed:
            self._arm_state["arm_elbow_flex.pos"] -= step

        if keys["wrist_flex_up"] in pressed:
            self._arm_state["arm_wrist_flex.pos"] += step
        if keys["wrist_flex_down"] in pressed:
            self._arm_state["arm_wrist_flex.pos"] -= step

        if keys["wrist_roll_left"] in pressed:
            self._arm_state["arm_wrist_roll.pos"] += step
        if keys["wrist_roll_right"] in pressed:
            self._arm_state["arm_wrist_roll.pos"] -= step

        if keys["gripper_open"] in pressed:
            self._arm_state["arm_gripper.pos"] += step
        if keys["gripper_close"] in pressed:
            self._arm_state["arm_gripper.pos"] -= step

        # Clip to joint limits
        self._arm_state["arm_shoulder_pan.pos"] = float(
            np.clip(self._arm_state["arm_shoulder_pan.pos"], *JOINT_LIMITS["shoulder_pan"])
        )
        self._arm_state["arm_shoulder_lift.pos"] = float(
            np.clip(self._arm_state["arm_shoulder_lift.pos"], *JOINT_LIMITS["shoulder_lift"])
        )
        self._arm_state["arm_elbow_flex.pos"] = float(
            np.clip(self._arm_state["arm_elbow_flex.pos"], *JOINT_LIMITS["elbow_flex"])
        )
        self._arm_state["arm_wrist_flex.pos"] = float(
            np.clip(self._arm_state["arm_wrist_flex.pos"], *JOINT_LIMITS["wrist_flex"])
        )
        self._arm_state["arm_wrist_roll.pos"] = float(
            np.clip(self._arm_state["arm_wrist_roll.pos"], *JOINT_LIMITS["wrist_roll"])
        )
        self._arm_state["arm_gripper.pos"] = float(
            np.clip(self._arm_state["arm_gripper.pos"], *JOINT_LIMITS["gripper"])
        )

        return self._arm_state.copy()

    # ------------------------------------------------------------------
    # Feedback & disconnect
    # ------------------------------------------------------------------

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        """No-op — keyboard teleoperator does not accept feedback."""

    def disconnect(self) -> None:
        """Stop the keyboard listener, leader arm, and release resources."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        if self._leader_arm is not None:
            self._leader_arm.disconnect()
            self._leader_arm = None
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        logger.info("%s disconnected.", self)
