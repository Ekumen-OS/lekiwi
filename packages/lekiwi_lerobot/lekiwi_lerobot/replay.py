import argparse
import logging
import time

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.utils.constants import ACTION
from lerobot.utils.robot_utils import busy_wait


def adapt_to_older_dataset(action: dict[str, float]) -> dict[str, float]:
    """Adapt action dictionary from older datasets to the current format."""
    # 1
    if "shoulder_pan" in action:
        action["arm_shoulder_pan.pos"] = action.pop("shoulder_pan")
    if "shoulder_lift" in action:
        action["arm_shoulder_lift.pos"] = action.pop("shoulder_lift")
    if "elbow_flex" in action:
        action["arm_elbow_flex.pos"] = action.pop("elbow_flex")
    if "wrist_flex" in action:
        action["arm_wrist_flex.pos"] = action.pop("wrist_flex")
    if "wrist_roll" in action:
        action["arm_wrist_roll.pos"] = action.pop("wrist_roll")
    if "gripper" in action:
        action["arm_gripper.pos"] = action.pop("gripper")
    # 2
    if "shoulder_pan.pos" in action:
        action["arm_shoulder_pan.pos"] = action.pop("shoulder_pan.pos")
    if "shoulder_lift.pos" in action:
        action["arm_shoulder_lift.pos"] = action.pop("shoulder_lift.pos")
    if "elbow_flex.pos" in action:
        action["arm_elbow_flex.pos"] = action.pop("elbow_flex.pos")
    if "wrist_flex.pos" in action:
        action["arm_wrist_flex.pos"] = action.pop("wrist_flex.pos")
    if "wrist_roll.pos" in action:
        action["arm_wrist_roll.pos"] = action.pop("wrist_roll.pos")
    if "gripper.pos" in action:
        action["arm_gripper.pos"] = action.pop("gripper.pos")

    return action


def main() -> None:
    """Main function to run the LeKiwi replay client."""
    parser = argparse.ArgumentParser(description="Run the LeKiwi replay client.")

    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        default="127.0.0.1",
        help="IP address of the robot (default: 127.0.0.1).",
    )
    parser.add_argument(
        "-l",
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO). Case-insensitive.",
    )
    parser.add_argument(
        "-e",
        "--episode",
        type=int,
        default=0,
        help="Index of the episode to replay (default: 0).",
    )
    parser.add_argument(
        "-r",
        "--repo-id",
        type=str,
        default="francocipollone/lekiwi_sim_cubes",
        help="Hugging Face repo ID of the dataset to replay. (default: francocipollone/lekiwi_sim_cubes)",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default="sandbox/datasets",
        help="Root directory where the dataset is stored (default: sandbox/datasets).",
    )
    args = parser.parse_args()
    log_level = args.level.upper()
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    robot_config = LeKiwiClientConfig(remote_ip=args.ip, id="lekiwi")
    robot = LeKiwiClient(robot_config)

    logging.info(f"Downloading dataset from {args.repo_id} into {args.directory}")
    root = args.directory + "/" + args.repo_id.split("/")[-1]
    root = root.replace("//", "/")
    episode_to_replay = args.episode
    dataset = LeRobotDataset(args.repo_id, root=root, episodes=[episode_to_replay])
    logging.info(f"Dataset stored at {root}")
    actions = dataset.hf_dataset.select_columns("action")
    # Filter dataset to only include frames from the specified episode since episodes are chunked in dataset V3.0
    episode_frames = dataset.hf_dataset.filter(lambda x: x["episode_index"] == episode_to_replay)
    actions = episode_frames.select_columns(ACTION)

    robot.connect()

    if not robot.is_connected:
        raise ValueError("Robot is not connected!")

    len_episodes_frames = len(episode_frames)
    logging.info(f"Replaying episode {args.episode} with {len_episodes_frames} frames.")
    for idx in range(len_episodes_frames):
        t0 = time.perf_counter()

        action = {name: float(actions[idx]["action"][i]) for i, name in enumerate(dataset.features["action"]["names"])}
        action = adapt_to_older_dataset(action)
        logging.debug(f"{action}")
        robot.send_action(action)

        busy_wait(max(1.0 / dataset.fps - (time.perf_counter() - t0), 0.0))

    robot.disconnect()


if __name__ == "__main__":
    main()
