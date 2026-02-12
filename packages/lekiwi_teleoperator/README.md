# lerobot\_teleoperator\_lekiwi\_keyboard

A **LeRobot teleoperator plugin** that provides full keyboard-based teleoperation
for the LeKiwi mobile manipulator (arm + omnidirectional base).

## Features

- **Arm control** – 6-DOF joint-by-joint positioning with configurable step sizes
  and joint limits.
- **Base control** – Omnidirectional movement (forward/backward, strafe, rotate)
  with multiple speed levels.
- **Optional leader arm** – When `leader_arm_port` is set, arm actions are read
  from a physical SO-101 leader arm instead of the keyboard.  The keyboard is
  always used for base movement.
- **Unified action** – A single `get_action()` call returns all 9 action keys
  expected by the LeKiwi robot (6 arm joints + 3 base velocities).
- **Zero-config** – Works out of the box with sensible defaults.  Every key
  binding and speed level is reconfigurable through `LeKiwiKeyboardTeleopConfig`.

## Installation

```bash
pip install lerobot_teleoperator_lekiwi_keyboard
```

Or, for development within the workspace:

```bash
pip install -e packages/lekiwi_teleoperator/
```

## Usage

Use with the standard `lerobot-teleoperate` CLI:

```bash
lerobot-teleoperate \
    --robot.type=lekiwi_mujoco \
    --teleop.type=lekiwi_keyboard
```

### With a leader arm

To use a physical SO-101 leader arm for arm control (keyboard still
handles the base):

```bash
lerobot-teleoperate \
    --robot.type=lekiwi_mujoco \
    --teleop.type=lekiwi_keyboard \
    --teleop.leader_arm_port=/dev/ttyACM0
```

### Default Key Bindings

#### Base movement

| Action       | Key |
|-------------|-----|
| Forward     | `W` |
| Backward    | `S` |
| Strafe left | `A` |
| Strafe right| `D` |
| Rotate left | `Z` |
| Rotate right| `X` |
| Speed up    | `R` |
| Speed down  | `F` |

#### Arm movement

| Joint          | Positive | Negative |
|---------------|----------|----------|
| Shoulder pan  | `G`      | `T`      |
| Shoulder lift | `Y`      | `H`      |
| Elbow flex    | `U`      | `J`      |
| Wrist flex    | `I`      | `K`      |
| Wrist roll    | `O`      | `L`      |
| Gripper       | `P`      | `;`      |

## Plugin Discovery

LeRobot discovers this package automatically at runtime because the
distribution name starts with `lerobot_teleoperator_`.  The config class
is registered under the key `"lekiwi_keyboard"` via
`@TeleoperatorConfig.register_subclass("lekiwi_keyboard")`.

## License

Apache-2.0
