import argparse
import logging

from lekiwi_lerobot.utils import record_loop
from lekiwi_teleoperate.teleoperate.arm import ArmTeleop
from lerobot.cameras.configs import CameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.teleoperators.keyboard import (
    KeyboardTeleop,
    KeyboardTeleopConfig,
)
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.constants import ACTION, OBS_STR
from lerobot.utils.control_utils import (
    init_keyboard_listener,
)
from lerobot.utils.visualization_utils import init_rerun

FPS = 30
EPISODE_TIME_SEC = 120
RESET_TIME_SEC = 10


def main() -> None:
    """Main function to run the LeKiwi recording client."""
    parser = argparse.ArgumentParser(description="Run the LeKiwi recording client.")
    parser.add_argument(
        "-l",
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO). Case-insensitive.",
    )
    parser.add_argument(
        "-i",
        "--ip",
        type=str,
        default="127.0.0.1",
        help="IP address of the robot (default: 127.0.0.1).",
    )
    parser.add_argument(
        "-r",
        "--repo-id",
        type=str,
        default=None,
        help="Hugging Face repo ID of the dataset to replay. (default: None)",
    )
    parser.add_argument(
        "-e",
        "--episodes",
        type=int,
        default=1,
        help=f"Number of episodes to record (default: {1}).",
    )
    parser.add_argument(
        "-t",
        "--task",
        type=str,
        default="Unnamed task",
        help="Task description to associate with each episode (default: 'Unnamed task').",
    )
    parser.add_argument(
        "--no-viz",
        action="store_false",
        dest="visualize",
        help="Disable Rerun visualization during recording.",
    )
    parser.add_argument(
        "-la",
        "--leader-arm",
        action="store_true",
        help="Use the leader arm for teleoperation (default: False).",
    )
    parser.add_argument(
        "--leader-arm-port",
        type=str,
        default="/dev/ttyACM0",
        help="Serial port for the leader arm (default: /dev/ttyACM0).",
    )

    args = parser.parse_args()
    if args.repo_id is None:
        raise ValueError(
            "A repo ID must be provided to store the dataset. This typically looks like 'hf_username/dataset_name'."
            "Remember to log in using Hugging Face CLI first."
        )

    log_level = args.level.upper()
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Camera config should match the one used in the robot config
    # when starting the robot host or simulation.
    #
    # Based on: --robot.cameras="{ front: {type: opencv, index_or_path: /dev/video0, width: 640, height: 480, fps: 30},
    # wrist: {type: opencv, index_or_path: /dev/video2, width: 640, height: 480, fps: 30}}"
    camera_config: dict[str, CameraConfig] = {
        "front": CameraConfig(width=640, height=480, fps=30),
        "wrist": CameraConfig(width=640, height=480, fps=30),
    }

    # Create the robot and teleoperator configurations
    robot_config = LeKiwiClientConfig(remote_ip=args.ip, id="lekiwi", cameras=camera_config)
    keyboard_config = KeyboardTeleopConfig()
    if args.leader_arm:
        teleop_arm_config = SO101LeaderConfig(port=args.leader_arm_port, id="lekiwi_leader_arm")

    robot = LeKiwiClient(robot_config)
    keyboard = KeyboardTeleop(keyboard_config)
    if args.leader_arm:
        leader_arm = SO101Leader(teleop_arm_config)
    else:
        arm_keyboard_handler = ArmTeleop()
    # Configure the dataset features
    action_features = hw_to_dataset_features(robot.action_features, ACTION)
    obs_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
    logging.info(f"Recording the following observation features: {list(obs_features.keys())}")
    logging.info(f"Recording the following action features: {list(action_features.keys())}")
    dataset_features = {**action_features, **obs_features}

    # Create the dataset
    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        fps=FPS,
        features=dataset_features,
        robot_type=robot.name,
        use_videos=True,
        image_writer_threads=4,
    )

    # To connect you already should have:
    #  - Real robot: this script running on LeKiwi:
    #    - `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
    #  - Sim robot: this script running on LeKiwi sim: `uv run lekiwi_sim --robot.id=my_awesome_kiwi`
    robot.connect()
    keyboard.connect()
    if args.leader_arm:
        leader_arm.connect()

    if args.visualize:
        logging.info("Initializing Rerun for visualization.")
        init_rerun(session_name="lekiwi_record")
    else:
        logging.info("Rerun visualization is disabled.")

    listener, events = init_keyboard_listener()

    if not robot.is_connected or not keyboard.is_connected:
        raise ValueError("Robot or keyboard is not connected!")
    if args.leader_arm and not leader_arm.is_connected:
        raise ValueError("Leader arm is not connected!")
    logging.info("Robot and keyboard are connected.")
    recorded_episodes = 0
    while recorded_episodes < args.episodes and not events["stop_recording"]:
        if not args.leader_arm:
            arm_keyboard_handler = ArmTeleop()
        logging.info(f"Recording episode {recorded_episodes}")
        # Run the record loop
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            dataset=dataset,
            keyboard_handler=keyboard,
            arm_keyboard_handler=leader_arm if args.leader_arm else arm_keyboard_handler,
            control_time_s=EPISODE_TIME_SEC,
            single_task=args.task,
            display_data=args.visualize,
        )

        # Reset the environment if not stopping or re-recording
        if not events["stop_recording"] and ((recorded_episodes < args.episodes - 1) or events["rerecord_episode"]):
            logging.info("Reset the environment")
            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                dataset=None,  # Don't record during reset phase
                keyboard_handler=keyboard,
                arm_keyboard_handler=leader_arm if args.leader_arm else arm_keyboard_handler,
                control_time_s=RESET_TIME_SEC,
                single_task=args.task,
                display_data=args.visualize,
            )

        if events["rerecord_episode"]:
            logging.info("Re-record episode")
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue

        logging.info(f"Saving episode number {recorded_episodes} to dataset.")
        dataset.save_episode()
        recorded_episodes += 1

    # Upload to hub and clean up
    dataset.finalize()
    dataset.push_to_hub()

    robot.disconnect()
    keyboard.disconnect()
    if args.leader_arm:
        leader_arm.disconnect()
    listener.stop()


if __name__ == "__main__":
    main()
