import logging
import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import _init_rerun, log_rerun_data

FPS = 30

COMMANDS_STR = """
Teleop commands:
Move:
      {forward}
    {left} {backward} {right}

Rotate:
    clockwise: {rotate_right}
    counter-clockwise: {rotate_left}

Speed:
    up: {speed_up}
    down: {speed_down}
"""


# TODO(arilow): Add teleoperation of the arm.
def main() -> None:
    """Main function to run the LeKiwi teleoperation client."""
    # Create the robot and teleoperator configurations
    robot_config = LeKiwiClientConfig(remote_ip="127.0.0.1", id="my_lekiwi")
    keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")

    robot = LeKiwiClient(robot_config)
    keyboard = KeyboardTeleop(keyboard_config)

    # To connect you already should have this script running on LeKiwi: `uv run lekiwi_sim`
    robot.connect()
    keyboard.connect()

    _init_rerun(session_name="lekiwi_teleop")

    if not robot.is_connected or not keyboard.is_connected:
        raise ValueError("Robot, leader arm of keyboard is not connected!")

    logging.info("Robot and keyboard are connected.")
    print(COMMANDS_STR.format(**robot_config.teleop_keys))

    while True:
        t0 = time.perf_counter()

        observation = robot.get_observation()

        keyboard_keys = keyboard.get_action()
        base_action = robot._from_keyboard_to_base_action(keyboard_keys)

        log_rerun_data(observation, {**base_action})

        action = {**base_action} if len(base_action) > 0 else {}

        robot.send_action(action)

        busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
