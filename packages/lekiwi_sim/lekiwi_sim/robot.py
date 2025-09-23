"""LeRobot Robot implementation for MuJoCo simulation with LeKiwi robot"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Any

import mujoco
import mujoco.viewer
import numpy as np
from lerobot.cameras.configs import CameraConfig
from lerobot.robots.robot import Robot

from .kinematics import LeKiwiMobileBase
from .utilities import get_scene_path, get_timestep_config


class ProtectedLeKiwiMujocoData:
    """A class to encapsulate and protect access to MuJoCo model and data."""

    def __init__(self) -> None:
        """Initialize the protected data with default values."""
        self.data = {
            "base_left_wheel_vel": 0.0,
            "base_back_wheel_vel": 0.0,
            "base_right_wheel_vel": 0.0,
            "shoulder_pan_joint_pos": 0.0,
            "shoulder_lift_joint_pos": 0.0,
            "elbow_flex_joint_pos": 0.0,
            "wrist_flex_joint_pos": 0.0,
            "wrist_roll_joint_pos": 0.0,
            "jaw_joint_pos": 0.0,
        }
        self.base_left_wheel_vel = 0.0
        self.base_back_wheel_vel = 0.0
        self.base_right_wheel_vel = 0.0
        self.shoulder_pan_joint_pos = 0.0
        self.shoulder_lift_joint_pos = 0.0
        self.elbow_flex_joint_pos = 0.0
        self.wrist_flex_joint_pos = 0.0
        self.wrist_roll_joint_pos = 0.0
        self.jaw_joint_pos = 0.0
        self.lock = threading.Lock()

    def get_action_data(self) -> dict[str, float]:
        """Get the current base wheel velocities.

        Returns:
            dict: A dictionary with the current wheel velocities.

        """
        with self.lock:
            return self.data.copy()

    def set_action_data(
        self,
        base_left_wheel_vel: float,
        base_back_wheel_vel: float,
        base_right_wheel_vel: float,
        shoulder_pan_joint_pos: float,
        shoulder_lift_joint_pos: float,
        elbow_flex_joint_pos: float,
        wrist_flex_joint_pos: float,
        wrist_roll_joint_pos: float,
        jaw_joint_pos: float,
    ) -> dict[str, float]:
        """Set the base wheel velocities.

        Args:
            base_left_wheel_vel (float): Velocity for the left wheel.
            base_back_wheel_vel (float): Velocity for the back wheel.
            base_right_wheel_vel (float): Velocity for the right wheel.
            shoulder_pan_joint_pos (float): Position for the shoulder pan joint.
            shoulder_lift_joint_pos (float): Position for the shoulder lift joint.
            elbow_flex_joint_pos (float): Position for the elbow flex joint.
            wrist_flex_joint_pos (float): Position for the wrist flex joint.
            wrist_roll_joint_pos (float): Position for the wrist roll joint.
            jaw_joint_pos (float): Position for the jaw joint.

        """
        with self.lock:
            self.data["base_left_wheel_vel"] = base_left_wheel_vel
            self.data["base_back_wheel_vel"] = base_back_wheel_vel
            self.data["base_right_wheel_vel"] = base_right_wheel_vel
            self.data["shoulder_pan_joint_pos"] = shoulder_pan_joint_pos
            self.data["shoulder_lift_joint_pos"] = shoulder_lift_joint_pos
            self.data["elbow_flex_joint_pos"] = elbow_flex_joint_pos
            self.data["wrist_flex_joint_pos"] = wrist_flex_joint_pos
            self.data["wrist_roll_joint_pos"] = wrist_roll_joint_pos
            self.data["jaw_joint_pos"] = jaw_joint_pos
            return self.data.copy()


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


def lekiwi_mujoco_cameras_config() -> dict[str, CameraConfig]:
    """Define the camera configurations for the LeKiwi MuJoCo simulation.

    Returns:
        dict: A dictionary with camera names as keys and CameraConfig objects as values.

    """
    return {
        "front": CameraConfig(
            fps=30,
            width=480,
            height=640,
        ),
        "wrist": CameraConfig(
            fps=30,
            width=480,
            height=640,
        ),
    }


@dataclass
class LeKiwiMujocoConfig:
    """Configuration for the LeKiwi MuJoCo simulation."""

    scene_path: str = get_scene_path()
    timestep: float = get_timestep_config()
    cameras: dict[str, CameraConfig] = field(default_factory=lekiwi_mujoco_cameras_config)


class LeKiwiMujoco(Robot):
    """LeKiwi Robot implementation for MuJoCo simulation."""

    MUJOCO_LEKIWI_BASE_CAMARA_NAME = "front"
    MUJOCO_LEKIWI_WRIST_CAMARA_NAME = "wrist"

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
        self.config = config
        self.cameras = config.cameras

    @property
    def _state_ft(self) -> dict[str, type]:
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

    @property
    def _cameras_ft(self) -> dict[str, tuple]:  # type: ignore
        return {cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras}

    @property
    def observation_features(self) -> dict[str, type | tuple]:  # type: ignore
        """A dictionary describing the structure and types of the observations provided by the robot."""
        return {**self._state_ft, **self._cameras_ft}

    def run_mujoco_loop(self) -> None:
        """Run the MuJoCo simulation loop in a separate thread."""
        self.mj_front_cam_renderer = mujoco.Renderer(self.mj_model, height=480, width=640)
        with mujoco.viewer.launch_passive(self.mj_model, self.mj_data) as viewer:
            while viewer.is_running() and self.mujoco_is_running:
                # Update action
                action_data = self.protected_lekiwi_data.get_action_data()
                logging.debug("Action to be applied to sim: %s", action_data)
                # Base wheel velocities.
                self.mj_data.actuator("base_back_wheel").ctrl[0] = action_data["base_back_wheel_vel"]
                self.mj_data.actuator("base_right_wheel").ctrl[0] = action_data["base_right_wheel_vel"]
                self.mj_data.actuator("base_left_wheel").ctrl[0] = action_data["base_left_wheel_vel"]
                # Arm joint positions.
                self.mj_data.actuator("Rotation").ctrl[0] = action_data["shoulder_pan_joint_pos"]
                self.mj_data.actuator("Pitch").ctrl[0] = action_data["shoulder_lift_joint_pos"]
                self.mj_data.actuator("Elbow").ctrl[0] = action_data["elbow_flex_joint_pos"]
                self.mj_data.actuator("Wrist_Pitch").ctrl[0] = action_data["wrist_flex_joint_pos"]
                self.mj_data.actuator("Wrist_Roll").ctrl[0] = action_data["wrist_roll_joint_pos"]
                self.mj_data.actuator("Jaw").ctrl[0] = action_data["jaw_joint_pos"]
                # Step simulation.
                mujoco.mj_step(self.mj_model, self.mj_data)

                # Update observation
                mobile_base_joint_velocities = [
                    self.mj_data.joint("base_left_wheel_joint").qvel[0],
                    self.mj_data.joint("base_right_wheel_joint").qvel[0],
                    self.mj_data.joint("base_back_wheel_joint").qvel[0],
                ]
                mobile_base_velocity = self.mobile_base_kinematics.forward_kinematics(
                    np.array(mobile_base_joint_velocities)
                )
                base_vel = {
                    "x.vel": mobile_base_velocity[0],
                    "y.vel": mobile_base_velocity[1],
                    "theta.vel": np.degrees(mobile_base_velocity[2]),
                }
                arm_state = {
                    "arm_shoulder_pan.pos": np.degrees(self.mj_data.joint("Rotation").qpos[0]),
                    "arm_shoulder_lift.pos": np.degrees(self.mj_data.joint("Pitch").qpos[0]),
                    "arm_elbow_flex.pos": np.degrees(self.mj_data.joint("Elbow").qpos[0]),
                    "arm_wrist_flex.pos": np.degrees(self.mj_data.joint("Wrist_Pitch").qpos[0]),
                    "arm_wrist_roll.pos": np.degrees(self.mj_data.joint("Wrist_Roll").qpos[0]),
                    "arm_gripper.pos": np.degrees(self.mj_data.joint("Jaw").qpos[0]),
                }
                self.mj_front_cam_renderer.update_scene(self.mj_data, camera=self.MUJOCO_LEKIWI_BASE_CAMARA_NAME)
                rgb_frame = self.mj_front_cam_renderer.render()
                camera_obs = {
                    "front": rgb_frame,
                    # TODO(francocipollone): Add wrist camera rendering.
                }
                self.protected_observation.set_observation({**arm_state, **base_vel, **camera_obs})

                logging.debug("Observation from sim: %s", self.protected_observation.get_observation())

                viewer.sync()

        self.mujoco_is_running = False

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

        return self.protected_lekiwi_data.set_action_data(
            base_left_wheel_vel=base_wheel_goal_vel[0],
            base_right_wheel_vel=base_wheel_goal_vel[1],
            base_back_wheel_vel=base_wheel_goal_vel[2],
            shoulder_pan_joint_pos=np.radians(action.get("arm_shoulder_pan.pos", 0.0)),
            shoulder_lift_joint_pos=np.radians(action.get("arm_shoulder_lift.pos", 0.0)),
            elbow_flex_joint_pos=np.radians(action.get("arm_elbow_flex.pos", 0.0)),
            wrist_flex_joint_pos=np.radians(action.get("arm_wrist_flex.pos", 0.0)),
            wrist_roll_joint_pos=np.radians(action.get("arm_wrist_roll.pos", 0.0)),
            jaw_joint_pos=action.get("arm_gripper.pos", 0.0),
        )

    def disconnect(self) -> None:
        """Disconnect from the robot and perform any necessary cleanup."""
        self.mujoco_is_running = False
        if self.simulation_thread.is_alive():
            self.simulation_thread.join()

    def stop_base(self) -> None:
        """Stop the robot's base movement immediately."""
        # TODO(arilow): Implement.
        return
