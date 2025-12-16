import argparse
import logging
import time

from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.factory import make_pre_post_processors
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiClientConfig
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.utils.constants import ACTION, OBS_STR
from lerobot.utils.control_utils import init_keyboard_listener, predict_action
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import get_safe_torch_device
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

FPS = 30


def main() -> None:
    """Main function to run a policy on the LeKiwi robot."""
    parser = argparse.ArgumentParser(description="Run a policy on the LeKiwi robot.")
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
        "-t",
        "--task",
        type=str,
        default="Unnamed task",
        help="Task description for the policy (default: 'Unnamed task').",
    )
    parser.add_argument(
        "-p",
        "--policy",
        type=str,
        default="francocipollone/act_lekiwi_sim_cubes",
        help="Hugging Face repo ID or local path of the policy to run.",
    )
    parser.add_argument(
        "--policy_type",
        type=str,
        default="act",
        help="Type of the policy to run (default: 'act').",
    )

    args = parser.parse_args()

    log_level = args.level.upper()
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.info(f"Loading policy from '{args.policy}'")
    if args.policy_type == "act":
        from lerobot.policies.act.modeling_act import ACTPolicy

        policy = ACTPolicy.from_pretrained(args.policy)
    elif args.policy_type == "smolvla":
        from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

        policy = SmolVLAPolicy.from_pretrained(args.policy)
    else:
        raise ValueError(f"Policy type '{args.policy_type}' not supported.")
    policy.reset()

    # Create the robot
    robot_config = LeKiwiClientConfig(remote_ip=args.ip, id="lekiwi")
    robot = LeKiwiClient(robot_config)

    # To connect you already should have:
    #  - Real robot: this script running on LeKiwi:
    #    - `python -m lerobot.robots.lekiwi.lekiwi_host --robot.id=my_awesome_kiwi`
    #  - Sim robot: this script running on LeKiwi sim: `uv run lekiwi_sim --robot.id=my_awesome_kiwi`
    robot.connect()

    if not robot.is_connected:
        raise ConnectionError("Robot is not connected!")

    logging.info("Robot is connected.")

    # Prepare for policy inference
    action_features = hw_to_dataset_features(robot.action_features, ACTION)
    obs_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
    dataset_features = {**action_features, **obs_features}
    device = get_safe_torch_device(policy.config.device)
    # Build Policy Processors
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=args.policy,
    )
    init_rerun(session_name="lekiwi_run_policy")

    listener, events = init_keyboard_listener()

    logging.info("Starting policy execution loop. Press 'q' to quit.")
    while not events["stop_recording"]:
        t0 = time.perf_counter()

        observation = robot.get_observation()

        observation_frame = build_dataset_frame(dataset_features, observation, prefix=OBS_STR)

        action_values = predict_action(
            observation_frame,
            policy,
            device,
            preprocessor,
            postprocessor,
            policy.config.use_amp,
            task=args.task,
            robot_type=robot.robot_type,
        )
        # As of LeRobot 0.4.0, the postprocessor returns a tensor that might have batch dimension
        # Remove batch dimension if present
        if action_values.dim() > 1:
            action_values = action_values.squeeze(0)

        action = {key: action_values[i].item() for i, key in enumerate(robot.action_features)}

        logging.debug(f"Predicted action: {action}")
        robot.send_action(action)

        log_rerun_data(observation, action)

        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))

    logging.info("Stopping policy execution.")
    robot.disconnect()
    listener.stop()


if __name__ == "__main__":
    main()
