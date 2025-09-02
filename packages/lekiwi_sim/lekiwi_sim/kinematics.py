import numpy as np


class LeKiwiMobileBase:
    """Class representing the mobile base of the LeKiwi robot.

    The mobile base holds the kinematics of a 3-wheeled omnidirectional robot.
    Where the wheels are placed at 120 degrees from each other.

    The wheel configuration is assumed to be:
    - Wheel 1 is at the "left", forming 30 degrees to the forward direction.
    - Wheel 2 is at the "right" clockwise 120 degrees from Wheel 1.
    - Wheel 3 is at the "back", clockwise 240 degrees from Wheel 1.
    """

    def __init__(self, wheel_radius: float, robot_base_radius: float) -> None:
        """Initialize the LeKiwiMobileBase.

        Args:
            wheel_radius (float): The radius of the wheels in meters.
            robot_base_radius (float): The distance from the center of rotation to each wheel in meters.

        """
        self.wheel_radius = wheel_radius
        self.robot_base_radius = robot_base_radius

        self.F_matrix = self._compute_forward_kinematics_matrix(self.wheel_radius, self.robot_base_radius)
        self.F_matrix_inv = np.linalg.inv(self.F_matrix)

    def forward_kinematics(self, wheel_speeds: np.ndarray) -> np.ndarray:
        """Compute the forward kinematics of the mobile base.

        Args:
            wheel_speeds (np.ndarray): Angular velocities of the wheels [left, right, back] in rad/s.

        Returns:
            np.ndarray: An array representing the robot's velocity [vx, vy, omega] in m/s and rad/s.

        """
        if wheel_speeds.shape != (3,):
            raise ValueError("wheel_speeds must be a numpy array of shape (3,)")

        # Compute the robot's velocity in the body frame
        return self.F_matrix @ wheel_speeds

    def inverse_kinematics(self, robot_velocity: np.ndarray) -> np.ndarray:
        """Compute the inverse kinematics of the mobile base.

        Args:
            robot_velocity (np.ndarray): The desired robot velocity [vx, vy, omega] in m/s and rad/s.

        Returns:
            np.ndarray: An array representing the angular velocities of the wheels [left, right, back] in rad/s.

        """
        if robot_velocity.shape != (3,):
            raise ValueError("robot_velocity must be a numpy array of shape (3,)")

        # Compute the wheel speeds required to achieve the desired robot velocity
        return self.F_matrix_inv @ robot_velocity

    @staticmethod
    def _compute_forward_kinematics_matrix(r: float, L: float) -> np.ndarray:
        """Calculates the forward kinematics transformation matrix for a 3-wheeled omni-drive robot.

        This matrix maps wheel speeds(angular velocities) to robot body speeds(linear and angular velocities)
        following the conventions:
        - The robot's forward direction is along the positive x-axis.
        - The robot's left direction is along the positive y-axis.
        - The robot's up direction is along the positive z-axis.
        - The robot's angular velocity (omega) is positive for counter-clockwise rotation when viewed from above.

        Args:
            r (float): The radius of each wheel (in meters).
            L (float): The radius of the robot base, from center to wheel (in meters).

        Returns:
            np.ndarray: A 3x3 transformation matrix that maps wheel speeds to robot body speeds.

        """
        return r * np.array(
            [[np.sqrt(3) / 2, -np.sqrt(3) / 2, 0], [-1 / 2, -1 / 2, 1], [-1 / (3 * L), -1 / (3 * L), -1 / (3 * L)]]
        )
