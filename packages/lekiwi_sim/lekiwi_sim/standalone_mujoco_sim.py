"""LeKiwi simulation on MuJoCo."""

import os
from importlib import resources

import mujoco
import mujoco.viewer


def get_scene_path() -> str:
    """Get the path to the MuJoCo scene file."""
    scene_path = resources.files("lekiwi_sim").joinpath("assets/scene.xml")
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


def main() -> None:
    """Execute the LeKiwi MuJoCo simulation."""
    try:
        mj_model = mujoco.MjModel.from_xml_path(get_scene_path())
        mj_model.opt.timestep = get_timestep_config()
        mj_data = mujoco.MjData(mj_model)
        with mujoco.viewer.launch_passive(mj_model, mj_data) as viewer:
            while viewer.is_running():
                mujoco.mj_step(mj_model, mj_data)
                viewer.sync()

    except KeyboardInterrupt:
        print("\nExiting simulation...")
    except Exception as e:
        print(f"Simulation error: {e}")
        raise e


if __name__ == "__main__":
    main()
