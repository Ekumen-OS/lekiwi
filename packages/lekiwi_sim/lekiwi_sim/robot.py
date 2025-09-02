"""LeRobot Robot implementation for MuJoCo simulation with LeKiwi robot"""

from dataclasses import dataclass
import threading
from typing import Any

import mujoco
import mujoco.viewer
import numpy as np
from lerobot.robots.robot import Robot

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

                wheel_state = self._wheel_rads_to_body(
                    self.mj_data.joint("base_left_wheel_joint").qvel[0],
                    self.mj_data.joint("base_back_wheel_joint").qvel[0],
                    self.mj_data.joint("base_right_wheel_joint").qvel[0],
                )

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
        print("Action received:", action)
        base_goal_vel = {k: v for k, v in action.items() if k.endswith(".vel")}

        base_wheel_goal_vel = self._body_to_wheel_rads(
            base_goal_vel["x.vel"], base_goal_vel["y.vel"], base_goal_vel["theta.vel"]
        )

        self.protected_lekiwi_data.set_base_data(
            base_wheel_goal_vel["base_left_wheel"],
            base_wheel_goal_vel["base_back_wheel"],
            base_wheel_goal_vel["base_right_wheel"],
        )
        print("Wheels vel:", base_wheel_goal_vel)

        return base_wheel_goal_vel

    def disconnect(self) -> None:
        """Disconnect from the robot and perform any necessary cleanup."""
        self.mujoco_is_running = False
        if self.simulation_thread.is_alive():
            self.simulation_thread.join()

    def stop_base(self) -> None:
        """Stop the robot's base movement immediately."""
        # TODO(arilow): Implement.
        return

    # TODO(https://github.com/ekumenlabs/lekiwi-dora/pull/11#discussion_r2310632598): Move this
    # to a kinematics module.
    def _body_to_wheel_rads(
        self,
        x: float,
        y: float,
        theta: float,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
        max_raw: int = 3000,
    ) -> dict[str, float]:
        """Convert desired body-frame velocities into wheel raw commands.

        Args:
          x      : Linear velocity in x (m/s).
          y      : Linear velocity in y (m/s).
          theta  : Rotational velocity (deg/s).
          wheel_radius: Radius of each wheel (meters).
          base_radius : Distance from the center of rotation to each wheel (meters).
          max_raw    : Maximum allowed raw command (ticks) per wheel.

        Returns:
          A dictionary with wheels angular speeds in rad/s as:
             {"base_left_wheel": value, "base_back_wheel": value, "base_right_wheel": value}.

        """
        # Convert rotational velocity from deg/s to rad/s.
        theta_rad = theta * (np.pi / 180.0)

        # Create the body velocity vector [x, y, theta_rad].
        velocity_vector = np.array([x, y, theta_rad])

        # Define the wheel mounting angles with a -90° offset.
        angles = np.radians(np.array([240, 0, 120]) - 90)
        # Build the kinematic matrix: each row maps body velocities to a wheel's linear speed.
        # The third column (base_radius) accounts for the effect of rotation.
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])

        # Compute each wheel's linear speed (m/s) and then its angular speed (rad/s).
        wheel_linear_speeds = m.dot(velocity_vector)
        wheel_angular_speeds = wheel_linear_speeds / wheel_radius

        # TODO(arilow): Find out why the wheels need to be inverted.
        corrected_wheel_angular_speeds = -wheel_angular_speeds
        return {
            "base_left_wheel": corrected_wheel_angular_speeds[0],
            "base_back_wheel": corrected_wheel_angular_speeds[1],
            "base_right_wheel": corrected_wheel_angular_speeds[2],
        }

    def _wheel_rads_to_body(
        self,
        left_wheel_speed: float,
        back_wheel_speed: float,
        right_wheel_speed: float,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
    ) -> dict[str, Any]:
        """Convert wheel raw command feedback back into body-frame velocities.

        Args:
        left_wheel_speed    : Left wheel velocity in rad/s
        back_wheel_speed    : Back wheel velocity in rad/s
        right_wheel_speed   : Right wheel velocity in rad/s
        wheel_radius: Radius of each wheel (meters).
        base_radius : Distance from the robot center to each wheel (meters).

        Returns:
        A dict (x.vel, y.vel, theta.vel) all in m/s

        """
        wheel_radps = np.array([left_wheel_speed, back_wheel_speed, right_wheel_speed])
        # Compute each wheel's linear speed (m/s) from its angular speed.
        wheel_linear_speeds = wheel_radps * wheel_radius

        # Define the wheel mounting angles with a -90° offset.
        angles = np.radians(np.array([240, 0, 120]) - 90)
        # TODO(https://github.com/ekumenlabs/lekiwi-dora/pull/11#discussion_r2310641980): Review kinematics here.
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])

        # Solve the inverse kinematics: body_velocity = M⁻¹ · wheel_linear_speeds.
        m_inv = np.linalg.inv(m)
        velocity_vector = m_inv.dot(wheel_linear_speeds)
        x, y, theta_rad = velocity_vector
        theta = theta_rad * (180.0 / np.pi)
        return {
            "x.vel": x,
            "y.vel": y,
            "theta.vel": theta,
        }  # m/s and deg/s
