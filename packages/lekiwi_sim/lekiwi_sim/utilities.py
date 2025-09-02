import os
from importlib import resources


def get_scene_path() -> str:
    """Get the path to the MuJoCo scene file."""
    scene_path = resources.files("lekiwi_sim").joinpath("assets/mjcf_lcmm_robot.xml")
    if not scene_path.is_file():
        raise FileNotFoundError(f"Scene file not found at {scene_path}. Please ensure the assets directory is present.")
    return str(scene_path)


def get_timestep_config() -> float:
    """Get the timestep configuration for the MuJoCo simulation."""
    try:
        timestep = float(os.getenv("TIMESTEP", "0.001"))
    except ValueError:
        raise ValueError from ValueError(f"Invalid TIMESTEP value: {timestep}. Must be a float.")
    return timestep
