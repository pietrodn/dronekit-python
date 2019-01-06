import logging
import time
import unittest

from pymavlink import mavutil

from dronekit import SystemStatus, VehicleMode, LocationGlobal
from dronekit.test.px4 import px4_vehicle

logging.basicConfig(level=logging.DEBUG)


class TestPX4(unittest.TestCase):

    def test_armed(self):
        with px4_vehicle() as vehicle:
            self.assertFalse(vehicle.armed)
            vehicle.arm()
            self.assertTrue(vehicle.armed)
            vehicle.disarm()
            self.assertFalse(vehicle.armed)

    def test_location(self):
        with px4_vehicle() as vehicle:
            vehicle.wait_ready('location')
            self.assertIsNotNone(vehicle.location.local_frame.north)

    def test_system_status(self):
        with px4_vehicle() as vehicle:
            vehicle.wait_ready('system_status')
            self.assertEqual(SystemStatus('STANDBY'), vehicle.system_status)
            self.assertEqual(vehicle.battery.level, 100)

    def test_mode(self):
        with px4_vehicle() as vehicle:
            self.assertEqual(VehicleMode('MANUAL'), vehicle.mode)

            vehicle.wait_ready('home_location')
            vehicle.mode = 'POSCTL'
            vehicle.wait_for_mode('POSCTL', 2)
            self.assertEqual(VehicleMode('POSCTL'), vehicle.mode)

    def test_home_location(self):
        with px4_vehicle() as vehicle:
            vehicle.home_location = LocationGlobal(-35, 149, 600)
            time.sleep(1)

            self.assertEqual(vehicle.home_location.lat, -35)
            self.assertEqual(vehicle.home_location.lon, 149)
            self.assertEqual(vehicle.home_location.alt, 600)

    def test_reboot(self):
        """Tries to reboot the vehicle, and checks that the autopilot ACKs the command."""

        with px4_vehicle() as vehicle:
            reboot_acks = []

            def on_ack(self, name, message):
                if message.command == 246:  # reboot/shutdown
                    reboot_acks.append(message)

            vehicle.add_message_listener('COMMAND_ACK', on_ack)
            vehicle.reboot()
            time.sleep(0.5)
            vehicle.remove_message_listener('COMMAND_ACK', on_ack)

            self.assertEqual(1, len(reboot_acks))  # one and only one ACK
            self.assertEqual(246, reboot_acks[0].command)  # for the correct command
            self.assertEqual(0, reboot_acks[0].result)  # the result must be successful

    def test_version(self):
        with px4_vehicle() as vehicle:
            self.assertEqual(mavutil.mavlink.MAV_AUTOPILOT_PX4, vehicle.version.autopilot_type)
            self.assertEqual(mavutil.mavlink.MAV_TYPE_QUADROTOR, vehicle.version.vehicle_type)

    def test_takeoff(self):
        with px4_vehicle() as vehicle:
            vehicle.wait_ready('home_location')




if __name__ == '__main__':
    unittest.main()
