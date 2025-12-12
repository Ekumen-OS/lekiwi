import argparse
import logging
import time

from lerobot.robots.lekiwi import LeKiwiClient, LeKiwiClientConfig
from lerobot.teleoperators.keyboard.teleop_keyboard import KeyboardTeleop, KeyboardTeleopConfig
from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.visualization_utils import init_rerun, log_rerun_data

from lekiwi_teleoperate.teleoperate.arm import ArmTeleop

FPS = 30

COMMANDS_STR = """
Teleop commands:
Base move:
           {forward}
    {left} {backward} {right}

Rotate:
    clockwise: {rotate_right}
    counter-clockwise: {rotate_left}

Speed:
    up: {speed_up}
    down: {speed_down}

Arm joint position:
    shoulder_pan_left: {shoulder_pan_left}
    shoulder_pan_right: {shoulder_pan_right}
    shoulder_lift_up: {shoulder_lift_up}
    shoulder_lift_down: {shoulder_lift_down}
    elbow_flex_up: {elbow_flex_up}
    elbow_flex_down: {elbow_flex_down}
    wrist_flex_up: {wrist_flex_up}
    wrist_flex_down: {wrist_flex_down}
    wrist_roll_left: {wrist_roll_left}
    wrist_roll_right: {wrist_roll_right}
    gripper_open: {gripper_open}
    gripper_close: {gripper_close}
"""


def main() -> None:
    """Main function to run the LeKiwi teleoperation client."""
    parser = argparse.ArgumentParser(description="Run the LeKiwi teleoperation client.")

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
    log_level = args.level.upper()
    logging.basicConfig(
        level=log_level, format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info("Configuring LeKiwi teleoperation client")

    # Create the robot and teleoperator configurations
    robot_config = LeKiwiClientConfig(remote_ip=args.ip, id="my_lekiwi")
    keyboard_config = KeyboardTeleopConfig(id="my_laptop_keyboard")
    if args.leader_arm:
        teleop_arm_config = SO101LeaderConfig(port=args.leader_arm_port, id="lekiwi_leader_arm")

    robot = LeKiwiClient(robot_config)
    keyboard = KeyboardTeleop(keyboard_config)

    # To connect you already should have this script running on LeKiwi: `uv run lekiwi_sim`
    robot.connect()
    keyboard.connect()
    if args.leader_arm:
        leader_arm = SO101Leader(teleop_arm_config)
        leader_arm.connect()
    else:
        arm_teleop = ArmTeleop()

    init_rerun(session_name="lekiwi_teleop")

    if not robot.is_connected:
        raise ValueError("Robot is not connected!")
    if not keyboard.is_connected:
        raise ValueError("Keyboard is not connected!")
    if args.leader_arm and not leader_arm.is_connected:
        raise ValueError("Leader arm is not connected!")

    logging.info("Robot and keyboard are connected.")
    print(COMMANDS_STR.format(**robot_config.teleop_keys, **ArmTeleop.ARM_TELEOP_KEYS))

    try:
        while True:
            t0 = time.perf_counter()

            observation = robot.get_observation()

            keyboard_keys = keyboard.get_action()
            base_action = robot._from_keyboard_to_base_action(keyboard_keys)
            if args.leader_arm:
                arm_action = leader_arm.get_action()
                arm_action = {f"arm_{k}": v for k, v in arm_action.items()}
            else:
                arm_action = arm_teleop.from_keyboard_to_arm_action(keyboard_keys)

            log_rerun_data(observation, {**arm_action, **base_action})

            action = {**base_action, **arm_action}  # Merge base and arm actions
            logging.debug("Sending action: %s", action)
            robot.send_action(action)

            busy_wait(max(1.0 / FPS - (time.perf_counter() - t0), 0.0))
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")

    finally:
        robot.disconnect()
        keyboard.disconnect()
        logging.info("LeKiwi teleoperation client has been disconnected.")


if __name__ == "__main__":
    main()
