import argparse
import logging
import time
from typing import Any

from lekiwi_teleoperate.teleoperate.arm import ArmTeleop
from lerobot.datasets.image_writer import safe_stop_image_writer
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient

# from lerobot.record import record_loop
from lerobot.teleoperators.keyboard import (
    KeyboardTeleop,
    KeyboardTeleopConfig,
)
from lerobot.utils.control_utils import (
    init_keyboard_listener,
    predict_action,
)
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import (
    get_safe_torch_device,
)
from lerobot.utils.visualization_utils import _init_rerun, log_rerun_data

FPS = 30
EPISODE_TIME_SEC = 30
RESET_TIME_SEC = 10


@safe_stop_image_writer  # type: ignore
def record_loop(
    robot: LeKiwiClient,
    events: dict[Any, Any],
    fps: int,
    dataset: LeRobotDataset | None = None,
    keyboard_handler: KeyboardTeleop | None = None,
    arm_keyboard_handler: ArmTeleop | None = None,
    policy: PreTrainedPolicy | None = None,
    control_time_s: int | None = None,
    single_task: str | None = None,
    display_data: bool = False,
) -> None:
    """Record loop for teleoperation or policy execution.

    This function is heavily influenced by the `lerobot.record.record_loop` function.
    The main differences are:
    - It supports both keyboard teleoperation and arm teleoperation.
    """
    if dataset is not None and dataset.fps != fps:
        raise ValueError(f"The dataset fps should be equal to requested fps ({dataset.fps} != {fps}).")

    if keyboard_handler is None:
        raise ValueError("A keyboard handler must be provided for teleoperation.")

    if arm_keyboard_handler is None:
        raise ValueError("An arm teleop must be provided for teleoperation.")

    if control_time_s is None:
        raise ValueError("A control time must be provided.")

    # if policy is given it needs cleaning up
    if policy is not None:
        policy.reset()

    timestamp = 0.0
    start_episode_t = time.perf_counter()
    while timestamp < control_time_s:
        start_loop_t = time.perf_counter()

        if events["exit_early"]:
            events["exit_early"] = False
            break

        observation = robot.get_observation()

        if policy is not None or dataset is not None:
            if dataset.features is None:  # type: ignore[union-attr]
                raise ValueError("Dataset features must be defined if using a dataset or a policy.")
            observation_frame = build_dataset_frame(dataset.features, observation, prefix="observation")  # type: ignore[union-attr]

        if policy is not None:
            action_values = predict_action(
                observation_frame,
                policy,
                get_safe_torch_device(policy.config.device),
                policy.config.use_amp,
                task=single_task,
                robot_type=robot.robot_type,
            )
            action = {key: action_values[i].item() for i, key in enumerate(robot.action_features)}
        elif policy is None and keyboard_handler is not None and arm_keyboard_handler is not None:
            pressed_keys = keyboard_handler.get_action()
            base_action = robot._from_keyboard_to_base_action(pressed_keys)
            arm_action = arm_keyboard_handler.from_keyboard_to_arm_action(pressed_keys)

            action = {**base_action, **arm_action}  # Merge base and arm actions
            logging.debug("Sending action: %s", action)

        else:
            logging.info(
                "No policy or teleoperator provided, skipping action generation."
                "This is likely to happen when resetting the environment without a teleop device."
                "The robot won't be at its rest position at the start of the next episode."
            )
            continue

        # Action can eventually be clipped using `max_relative_target`,
        # so action actually sent is saved in the dataset.
        sent_action = robot.send_action(action)

        if dataset is not None:
            action_frame = build_dataset_frame(dataset.features, sent_action, prefix="action")
            frame = {**observation_frame, **action_frame}
            dataset.add_frame(frame, task=single_task)

        if display_data:
            log_rerun_data(observation, action)

        dt_s = time.perf_counter() - start_loop_t
        busy_wait(1 / fps - dt_s)

        timestamp = time.perf_counter() - start_episode_t


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

    # Create the robot and teleoperator configurations
    robot_config = LeKiwiClientConfig(remote_ip="127.0.0.1", id="lekiwi")
    keyboard_config = KeyboardTeleopConfig()

    robot = LeKiwiClient(robot_config)
    keyboard = KeyboardTeleop(keyboard_config)
    arm_keyboard_handler = ArmTeleop()
    # Configure the dataset features
    action_features = hw_to_dataset_features(robot.action_features, "action")
    obs_features = hw_to_dataset_features(robot.observation_features, "observation")

    # TODO(francocipollone): Use wrist camera information as well.
    obs_features.pop("observation.images.wrist")
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
        image_writer_threads=0,
    )

    # To connect you already should have:
    #  - Real robot: this script running on LeKiwi:
    #    - `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
    #  - Sim robot: this script running on LeKiwi sim: `uv run lekiwi_sim --robot.id=my_awesome_kiwi`
    robot.connect()
    keyboard.connect()

    _init_rerun(session_name="lekiwi_record")

    listener, events = init_keyboard_listener()

    if not robot.is_connected or not keyboard.is_connected:
        raise ValueError("Robot or keyboard is not connected!")
    logging.info("Robot and keyboard are connected.")
    recorded_episodes = 0
    while recorded_episodes < args.episodes and not events["stop_recording"]:
        logging.info(f"Recording episode {recorded_episodes}")
        # Run the record loop
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            dataset=dataset,
            keyboard_handler=keyboard,
            arm_keyboard_handler=arm_keyboard_handler,
            control_time_s=EPISODE_TIME_SEC,
            single_task=args.task,
            display_data=True,
        )

        # Logic for reset env
        if not events["stop_recording"] and ((recorded_episodes < args.episodes - 1) or events["rerecord_episode"]):
            logging.info("Reset the environment")
            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                keyboard_handler=keyboard,
                arm_keyboard_handler=arm_keyboard_handler,
                control_time_s=RESET_TIME_SEC,
                single_task=args.task,
                display_data=True,
            )

        if events["rerecord_episode"]:
            logging.info("Re-record episode")
            events["rerecord_episode"] = False
            events["exit_early"] = False
            dataset.clear_episode_buffer()
            continue

        dataset.save_episode()
        recorded_episodes += 1

    # Upload to hub and clean up
    dataset.push_to_hub()

    robot.disconnect()
    keyboard.disconnect()
    listener.stop()


if __name__ == "__main__":
    main()
