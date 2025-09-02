import numpy as np
import pytest
from lekiwi_sim.kinematics import LeKiwiMobileBase

ROBOT_BASE_RADIUS = 0.125  # meters
WHEEL_RADIUS = 0.05  # meters


@pytest.fixture  # type: ignore
def mobile_base() -> LeKiwiMobileBase:
    """Fixture for LeKiwiMobileBase instance."""
    return LeKiwiMobileBase(wheel_radius=WHEEL_RADIUS, robot_base_radius=ROBOT_BASE_RADIUS)


class TestLeKiwiMobileBase:
    """Test suite for the LeKiwiMobileBase kinematics."""

    def test_initialization(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test the initialization of the LeKiwiMobileBase."""
        assert mobile_base.wheel_radius == WHEEL_RADIUS
        assert mobile_base.robot_base_radius == ROBOT_BASE_RADIUS
        assert mobile_base.F_matrix.shape == (3, 3)
        assert mobile_base.F_matrix_inv.shape == (3, 3)

        # Check if F_matrix_inv is indeed the inverse of F_matrix
        identity_matrix = np.identity(3)
        computed_identity = mobile_base.F_matrix @ mobile_base.F_matrix_inv
        np.testing.assert_allclose(computed_identity, identity_matrix, atol=1e-9)

    def test_forward_kinematics_pure_forward(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test forward kinematics for pure forward motion (along x-axis)."""
        # For pure forward motion (vx > 0, vy=0, omega=0), we need phi_l = -phi_r and phi_b = 0.
        wheel_speeds = np.array([10.0, -10.0, 0.0])
        robot_velocity = mobile_base.forward_kinematics(wheel_speeds)

        assert robot_velocity[0] > 0
        np.testing.assert_allclose(robot_velocity[1], 0, atol=1e-9)
        np.testing.assert_allclose(robot_velocity[2], 0, atol=1e-9)

    def test_forward_kinematics_pure_sideways(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test forward kinematics for pure sideways motion (along y-axis)."""
        # For pure sideways motion (vx=0, vy>0, omega=0), we need phi_l = phi_r and phi_b = -2*phi_l.
        # To get vy > 0, we need phi_l < 0.
        wheel_speeds = np.array([-5.0, -5.0, 10.0])
        robot_velocity = mobile_base.forward_kinematics(wheel_speeds)

        np.testing.assert_allclose(robot_velocity[0], 0, atol=1e-9)
        assert robot_velocity[1] > 0
        np.testing.assert_allclose(robot_velocity[2], 0, atol=1e-9)

    def test_forward_kinematics_pure_rotation(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test forward kinematics for pure rotation (CW)."""
        # All wheels rotating with the same positive speed should result in CW rotation.
        wheel_speeds = np.array([5.0, 5.0, 5.0])
        robot_velocity = mobile_base.forward_kinematics(wheel_speeds)

        np.testing.assert_allclose(robot_velocity[0], 0, atol=1e-9)
        np.testing.assert_allclose(robot_velocity[1], 0, atol=1e-9)
        # Omega should be negative (CW).
        assert robot_velocity[2] < 0

    def test_inverse_kinematics_pure_forward(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test inverse kinematics for pure forward motion."""
        robot_velocity = np.array([1.0, 0.0, 0.0])  # vx=1 m/s
        wheel_speeds = mobile_base.inverse_kinematics(robot_velocity)
        reconstructed_velocity = mobile_base.forward_kinematics(wheel_speeds)
        np.testing.assert_allclose(reconstructed_velocity, robot_velocity, atol=1e-9)

    def test_inverse_kinematics_pure_sideways(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test inverse kinematics for pure sideways motion."""
        robot_velocity = np.array([0.0, 1.0, 0.0])  # vy=1 m/s
        wheel_speeds = mobile_base.inverse_kinematics(robot_velocity)
        reconstructed_velocity = mobile_base.forward_kinematics(wheel_speeds)
        np.testing.assert_allclose(reconstructed_velocity, robot_velocity, atol=1e-9)

    def test_inverse_kinematics_pure_rotation(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test inverse kinematics for pure rotation."""
        robot_velocity = np.array([0.0, 0.0, 1.0])  # omega=1 rad/s (CW)
        wheel_speeds = mobile_base.inverse_kinematics(robot_velocity)
        reconstructed_velocity = mobile_base.forward_kinematics(wheel_speeds)
        np.testing.assert_allclose(reconstructed_velocity, robot_velocity, atol=1e-9)
        # For CW rotation, all wheel speeds should be negative and equal.
        assert np.all(wheel_speeds < 0)
        assert np.isclose(wheel_speeds[0], wheel_speeds[1])
        assert np.isclose(wheel_speeds[1], wheel_speeds[2])

    def test_round_trip_consistency(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test if FK(IK(v)) == v and IK(FK(w)) == w."""
        # Test 1: velocity -> wheels -> velocity
        robot_velocity = np.array([0.5, -0.2, 0.8])
        wheel_speeds = mobile_base.inverse_kinematics(robot_velocity)
        reconstructed_velocity = mobile_base.forward_kinematics(wheel_speeds)
        np.testing.assert_allclose(robot_velocity, reconstructed_velocity, atol=1e-9)

        # Test 2: wheels -> velocity -> wheels
        wheel_speeds = np.array([10.0, 5.0, -8.0])
        robot_velocity = mobile_base.forward_kinematics(wheel_speeds)
        reconstructed_speeds = mobile_base.inverse_kinematics(robot_velocity)
        np.testing.assert_allclose(wheel_speeds, reconstructed_speeds, atol=1e-9)

    def test_invalid_input_shape(self, mobile_base: LeKiwiMobileBase) -> None:
        """Test that invalid input shapes raise ValueError."""
        with pytest.raises(ValueError, match="wheel_speeds must be a numpy array of shape \\(3,\\)"):
            mobile_base.forward_kinematics(np.array([1.0, 2.0]))
        with pytest.raises(ValueError, match="wheel_speeds must be a numpy array of shape \\(3,\\)"):
            mobile_base.forward_kinematics(np.array([1.0, 2.0, 3.0, 4.0]))
        with pytest.raises(ValueError, match="robot_velocity must be a numpy array of shape \\(3,\\)"):
            mobile_base.inverse_kinematics(np.array([1.0, 2.0]))
        with pytest.raises(ValueError, match="robot_velocity must be a numpy array of shape \\(3,\\)"):
            mobile_base.inverse_kinematics(np.array([1.0, 2.0, 3.0, 4.0]))
