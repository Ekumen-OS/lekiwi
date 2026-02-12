"""LeRobot third-party robot plugin for MuJoCo simulation of the LeKiwi robot.

Importing this package registers the ``lekiwi_mujoco`` robot type with LeRobot's
plugin system via ``@RobotConfig.register_subclass("lekiwi_mujoco")``.
"""

from .config_lekiwi_mujoco import LeKiwiMujocoConfig, MuJoCoCameraConfig
from .lekiwi_mujoco import LeKiwiMujoco

__all__ = ["LeKiwiMujoco", "LeKiwiMujocoConfig", "MuJoCoCameraConfig"]
