import logging
import time
from typing import Any, Union

from lekiwi_teleoperate.teleoperate.arm import ArmTeleop
from lerobot.datasets.image_writer import safe_stop_image_writer
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import build_dataset_frame
from lerobot.policies.pretrained import PreTrainedPolicy
from lerobot.processor import (
    PolicyAction,
    PolicyProcessorPipeline,
)
from lerobot.robots.lekiwi.lekiwi_client import LeKiwiClient
from lerobot.teleoperators.keyboard import (
    KeyboardTeleop,
)
from lerobot.teleoperators.so101_leader import SO101Leader
from lerobot.utils.control_utils import (
    predict_action,
)
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import (
    get_safe_torch_device,
)
from lerobot.utils.visualization_utils import log_rerun_data


@safe_stop_image_writer  # type: ignore
def record_loop(
    robot: LeKiwiClient,
    events: dict[Any, Any],
    fps: int,
    dataset: LeRobotDataset | None = None,
    keyboard_handler: KeyboardTeleop | None = None,
    arm_keyboard_handler: Union[ArmTeleop, SO101Leader, None] = None,
    policy: PreTrainedPolicy | None = None,
    preprocessor: PolicyProcessorPipeline[dict[str, Any], dict[str, Any]] | None = None,
    postprocessor: PolicyProcessorPipeline[PolicyAction, PolicyAction] | None = None,
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

    if display_data:
        logging.info("Visualizing data with Rerun.")
    else:
        logging.info("Not visualizing data.")

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

        if policy is not None and preprocessor is not None and postprocessor is not None:
            action_values = predict_action(
                observation=observation_frame,
                policy=policy,
                device=get_safe_torch_device(policy.config.device),
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                use_amp=policy.config.use_amp,
                task=single_task,
                robot_type=robot.robot_type,
            )
            if action_values.dim() > 1:
                action_values = action_values.squeeze(0)
            action = {key: action_values[i].item() for i, key in enumerate(robot.action_features)}
            print(f"Predicted action: {action}")
        elif policy is None and keyboard_handler is not None and arm_keyboard_handler is not None:
            pressed_keys = keyboard_handler.get_action()
            base_action = robot._from_keyboard_to_base_action(pressed_keys)

            # Handle both ArmTeleop (keyboard-based) and SO101Leader (physical arm)
            if isinstance(arm_keyboard_handler, SO101Leader):
                arm_action = arm_keyboard_handler.get_action()
                arm_action = {f"arm_{k}": v for k, v in arm_action.items()}
            else:
                arm_action = arm_keyboard_handler.from_keyboard_to_arm_action(pressed_keys)

            action = {**base_action, **arm_action}  # Merge base and arm actions
            # TODO(francocipollone): We would probably want to use the teleop_action_processor here.
            # action = teleop_action_processor((action, observation))
            logging.debug("Sending action: %s", action)

        else:
            logging.info(
                "No policy or teleoperator provided, skipping action generation."
                "This is likely to happen when resetting the environment without a teleop device."
                "The robot won't be at its rest position at the start of the next episode."
            )
            continue

        # TODO(francocipollone): We would probably want to use the robot_action_processor here before sending the action
        sent_action = robot.send_action(action)

        if dataset is not None:
            action_frame = build_dataset_frame(dataset.features, sent_action, prefix="action")
            frame = {**observation_frame, **action_frame, "task": single_task}
            dataset.add_frame(frame)

        if display_data:
            log_rerun_data(observation, action)

        dt_s = time.perf_counter() - start_loop_t
        busy_wait(1 / fps - dt_s)

        timestamp = time.perf_counter() - start_episode_t
