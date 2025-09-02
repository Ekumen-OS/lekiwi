"""LeRobot Robot implementation for MuJoCo simulation with LeKiwi robot"""

import logging
import threading
from dataclasses import dataclass
from typing import Any

import mujoco
import mujoco.viewer
import numpy as np
from lerobot.robots.robot import Robot

from .kinematics import LeKiwiMobileBase
from .utilities import get_scene_path, get_timestep_config


class ProtectedLeKiwiMujocoData:
    """A class to encapsulate and protect access to MuJoCo model and data."""

    def __init__(self) -> None:
        """Initialize the protected data with default values."""
        self.base_left_wheel_vel = 0.0
        self.base_back_wheel_vel = 0.0
        self.base_right_wheel_vel = 0.0
        self.lock = threading.Lock()

    def get_base_data(self) -> dict[str, float]:
        """Get the current base wheel velocities.

        Returns:
            dict: A dictionary with the current wheel velocities.

        """
        with self.lock:
            return {
                "base_left_wheel_vel": self.base_left_wheel_vel,
                "base_back_wheel_vel": self.base_back_wheel_vel,
                "base_right_wheel_vel": self.base_right_wheel_vel,
            }

    def set_base_data(
        self, base_left_wheel_vel: float, base_back_wheel_vel: float, base_right_wheel_vel: float
    ) -> None:
        """Set the base wheel velocities.

        Args:
            base_left_wheel_vel (float): Velocity for the left wheel.
            base_back_wheel_vel (float): Velocity for the back wheel.
            base_right_wheel_vel (float): Velocity for the right wheel.

        """
        with self.lock:
            self.base_left_wheel_vel = base_left_wheel_vel
            self.base_back_wheel_vel = base_back_wheel_vel
            self.base_right_wheel_vel = base_right_wheel_vel


class ProtectedLeKiwiMujocoObservation:
    """A class to encapsulate and protect access to MuJoCo observations."""

    def __init__(self) -> None:
        """Initialize the protected observation with default values."""
        self.observation: dict[str, float] = {}
        self.lock = threading.Lock()

    def get_observation(self) -> dict[str, float]:
        """Get the current observation.

        Returns:
            dict: A dictionary with the current observation.

        """
        with self.lock:
            return self.observation.copy()

    def set_observation(self, observation: dict[str, Any]) -> None:
        """Set the current observation.

        Args:
            observation (dict): A dictionary with the new observation values.

        """
        with self.lock:
            self.observation = observation.copy()

    def get_observed_joints(self) -> list[str]:
        """Return a list of joint names that are observed.

        Returns:
            list[str]: A list of joint names.

        """
        return [
            "base_left_wheel_joint",
            "base_back_wheel_joint",
            "base_right_wheel_joint",
            "arm_joint_1",
            "arm_joint_2",
            "arm_joint_3",
            "arm_joint_4",
            "arm_joint_5",
            "arm_joint_6",
        ]


@dataclass
class LeKiwiMujocoConfig:
    """Configuration for the LeKiwi MuJoCo simulation."""

    scene_path: str = get_scene_path()
    timestep: float = get_timestep_config()


class LeKiwiMujoco(Robot):
    """LeKiwi Robot implementation for MuJoCo simulation."""

    def __init__(self, config: LeKiwiMujocoConfig) -> None:
        """Initialize the MuJoCo simulation environment"""
        self.protected_lekiwi_data = ProtectedLeKiwiMujocoData()
        self.protected_observation = ProtectedLeKiwiMujocoObservation()
        self.mj_model = mujoco.MjModel.from_xml_path(config.scene_path)
        self.mj_model.opt.timestep = config.timestep
        self.mj_data = mujoco.MjData(self.mj_model)
        self.simulation_thread = threading.Thread(target=self.run_mujoco_loop, daemon=True)
        self.mujoco_is_running = False
        self.mobile_base_kinematics = LeKiwiMobileBase(wheel_radius=0.05, robot_base_radius=0.125)

    def run_mujoco_loop(self) -> None:
        """Run the MuJoCo simulation loop in a separate thread."""
        with mujoco.viewer.launch_passive(self.mj_model, self.mj_data) as viewer:
            while viewer.is_running() and self.mujoco_is_running:
                base_data = self.protected_lekiwi_data.get_base_data()
                self.mj_data.actuator("base_back_wheel").ctrl[0] = base_data["base_back_wheel_vel"]
                self.mj_data.actuator("base_right_wheel").ctrl[0] = base_data["base_right_wheel_vel"]
                self.mj_data.actuator("base_left_wheel").ctrl[0] = base_data["base_left_wheel_vel"]
                mujoco.mj_step(self.mj_model, self.mj_data)

                observed_joints_names = self.protected_observation.get_observed_joints()

                arm_state = {}
                for joint_name in observed_joints_names:
                    if joint_name.startswith("arm_"):
                        arm_state[f"{joint_name}.pos"] = self.mj_data.joint(joint_name).qpos[0]

                mobile_base_joint_velocities = [
                    self.mj_data.joint("base_left_wheel_joint").qvel[0],
                    self.mj_data.joint("base_right_wheel_joint").qvel[0],
                    self.mj_data.joint("base_back_wheel_joint").qvel[0],
                ]
                mobile_base_velocity = self.mobile_base_kinematics.forward_kinematics(
                    np.array(mobile_base_joint_velocities)
                )
                wheel_state = {
                    "x.vel": mobile_base_velocity[0],
                    "y.vel": mobile_base_velocity[1],
                    "theta.vel": np.degrees(mobile_base_velocity[2]),
                }

                self.protected_observation.set_observation({**arm_state, **wheel_state})

                viewer.sync()

        self.mujoco_is_running = False

    @property
    def observation_features(self) -> dict[str, Any]:
        """A dictionary describing the structure and types of the observations produced by the robot.

        Its structure (keys) should match the structure of what is returned by :pymeth:`get_observation`.
        Values for the dict should either be:
            - The type of the value if it's a simple value, e.g. `float` for single proprioceptive
              value (a joint's position/velocity)
            - A tuple representing the shape if it's an array-type value, e.g. `(height, width, channel)` for images

        Note: this property should be able to be called regardless of whether the robot is connected or not.

        Returns:
            dict: A dictionary with observation features.

        """
        # TODO(arilow): Implement.
        return {}

    @property
    def action_features(self) -> dict[str, Any]:
        """A dictionary describing the structure and types of the actions expected by the robot.

        Its structure (keys) should match the structure of what is passed to :pymeth:`send_action`. Values for the dict
        should be the type of the value if it's a simple value, e.g. `float` for single proprioceptive value
        (a joint's goal position/velocity)

        Note: this property should be able to be called regardless of whether the robot is connected or not.

        Returns:
            dict: A dictionary with action features.

        """
        # TODO(arilow): Implement.
        return {}

    @property
    def is_connected(self) -> bool:
        """Whether the robot is currently connected or not.

        If `False`, calling :pymeth:`get_observation` or :pymeth:`send_action` should raise an error.

        Returns:
            bool: True if the robot is connected, False otherwise.

        """
        return self.mujoco_is_running

    def connect(self, calibrate: bool = True) -> None:
        """Establish communication with the robot.

        Args:
            calibrate (bool): If True, automatically calibrate the robot after connecting if it's not
                calibrated or needs calibration (this is hardware-dependant).

        """
        self.mujoco_is_running = True
        self.simulation_thread.start()

    @property
    def is_calibrated(self) -> bool:
        """Whether the robot is currently calibrated or not. Should be always `True` if not applicable

        Returns:
            bool: True if the robot is calibrated, False otherwise.

        """
        # TODO(arilow): Implement.
        return False

    def calibrate(self) -> None:
        """Calibrate the robot if applicable. If not, this should be a no-op.

        This method should collect any necessary data (e.g., motor offsets) and update the
        :pyattr:`calibration` dictionary accordingly.
        """
        # TODO(arilow): Implement.
        return

    def configure(self) -> None:
        """Apply any one-time or runtime configuration to the robot.

        This may include setting motor parameters, control modes, or initial state.
        """
        # TODO(arilow): Implement.
        return

    def get_observation(self) -> dict[str, Any]:
        """Retrieve the current observation from the robot.

        Returns:
            dict[str, Any]: A flat dictionary representing the robot's current sensory state. Its structure
                should match :pymeth:`observation_features`.

        """
        return self.protected_observation.get_observation()

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send an action command to the robot.

        Args:
            action (dict[str, Any]): Dictionary representing the desired action. Its structure should match
                :pymeth:`action_features`.

        Returns:
            dict[str, Any]: The action actually sent to the motors potentially clipped or modified, e.g. by
                safety limits on velocity.

        """
        logging.debug("Action received: %s", action)
        base_goal_vel = {k: v for k, v in action.items() if k.endswith(".vel")}

        base_wheel_goal_vel = self.mobile_base_kinematics.inverse_kinematics(
            np.array(
                [
                    base_goal_vel.get("x.vel", 0.0),
                    base_goal_vel.get("y.vel", 0.0),
                    np.radians(base_goal_vel.get("theta.vel", 0.0)),
                ]
            )
        )

        self.protected_lekiwi_data.set_base_data(
            base_left_wheel_vel=base_wheel_goal_vel[0],
            base_right_wheel_vel=base_wheel_goal_vel[1],
            base_back_wheel_vel=base_wheel_goal_vel[2],
        )
        logging.debug("Set wheel velocities to: %s", base_wheel_goal_vel)

        return {
            "base_left_wheel_vel": base_wheel_goal_vel[0],
            "base_right_wheel_vel": base_wheel_goal_vel[1],
            "base_back_wheel_vel": base_wheel_goal_vel[2],
        }

    def disconnect(self) -> None:
        """Disconnect from the robot and perform any necessary cleanup."""
        self.mujoco_is_running = False
        if self.simulation_thread.is_alive():
            self.simulation_thread.join()

    def stop_base(self) -> None:
        """Stop the robot's base movement immediately."""
        # TODO(arilow): Implement.
        return
