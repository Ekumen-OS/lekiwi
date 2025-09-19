import argparse
import logging
import time

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.utils.robot_utils import busy_wait


def main() -> None:
    """Main function to run the LeKiwi replay client."""
    parser = argparse.ArgumentParser(description="Run the LeKiwi replay client.")

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
        default="francocipollone/lekiwi_test",
        help="Hugging Face repo ID of the dataset to replay. (default: francocipollone/lekiwi_test)",
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

    robot_config = LeKiwiClientConfig(remote_ip="127.0.0.1", id="lekiwi")
    robot = LeKiwiClient(robot_config)

    logging.info(f"Downloading dataset from {args.repo_id} into {args.directory}")
    root = args.directory + "/" + args.repo_id.split("/")[-1]
    root = root.replace("//", "/")
    dataset = LeRobotDataset(args.repo_id, root=root, episodes=[args.episode])
    logging.info(f"Dataset stored at {root}")
    actions = dataset.hf_dataset.select_columns("action")

    robot.connect()

    if not robot.is_connected:
        raise ValueError("Robot is not connected!")

    logging.info(f"Replaying episode {args.episode} with {dataset.num_frames} frames.")
    for idx in range(dataset.num_frames):
        t0 = time.perf_counter()

        action = {name: float(actions[idx]["action"][i]) for i, name in enumerate(dataset.features["action"]["names"])}
        robot.send_action(action)

        busy_wait(max(1.0 / dataset.fps - (time.perf_counter() - t0), 0.0))

    robot.disconnect()


if __name__ == "__main__":
    main()
