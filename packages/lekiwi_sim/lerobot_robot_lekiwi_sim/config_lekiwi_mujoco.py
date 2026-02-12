"""Configuration for the LeKiwi MuJoCo simulation robot plugin."""

from dataclasses import dataclass, field

from lerobot.cameras.configs import CameraConfig
from lerobot.robots.config import RobotConfig


@CameraConfig.register_subclass("mujoco")
@dataclass(kw_only=True)
class MuJoCoCameraConfig(CameraConfig):
    """Camera configuration for MuJoCo-rendered cameras.

    This is a simple concrete subclass of CameraConfig that holds
    the resolution and fps metadata for cameras rendered by MuJoCo.
    No physical device is involved — rendering happens inside the simulation loop.
    """


def lekiwi_mujoco_cameras_config() -> dict[str, CameraConfig]:
    """Define the default camera configurations for the LeKiwi MuJoCo simulation.

    Returns:
        dict: A dictionary with camera names as keys and MuJoCoCameraConfig objects as values.

    """
    return {
        "front": MuJoCoCameraConfig(
            fps=30,
            width=480,
            height=640,
        ),
        "wrist": MuJoCoCameraConfig(
            fps=30,
            width=480,
            height=640,
        ),
    }


@RobotConfig.register_subclass("lekiwi_mujoco")
@dataclass(kw_only=True)
class LeKiwiMujocoConfig(RobotConfig):
    """Configuration for the LeKiwi MuJoCo simulation."""

    scene_path: str | None = None
    timestep: float | None = None
    cameras: dict[str, CameraConfig] = field(default_factory=lekiwi_mujoco_cameras_config)
