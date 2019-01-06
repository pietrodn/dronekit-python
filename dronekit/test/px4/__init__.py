import logging
import socket
import subprocess
import time
from contextlib import contextmanager

import dronekit


class PX4RunnerException(Exception):
    """A problem occurred with the PX4 Docker image!"""


class PX4Runner:

    docker_image = "pietrodn/px4_gazebo_docker:latest"

    def __init__(self, udp_port=14557, timeout=10):
        self.port = udp_port
        self.timeout = timeout
        self._logger = logging.getLogger(__name__)

    def wait_for_simulation(self, timeout=30):
        start_time = time.time()

        while time.time() - start_time < timeout:
            line = self._process.stdout.readline()
            if b"[mavlink] mode: Onboard" in line:
                return True

        return False

    def __enter__(self):
        self._logger.info("Initiating PX4 simulation...")
        self._process = subprocess.Popen(
            [
                "docker", "run", "-i", "--init", "-p", "{}:14556/udp".format(self.port),
                self.docker_image
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        if not self.wait_for_simulation(self.timeout):
            raise PX4RunnerException("PX4 simulator is not ready!")

        self._logger.info("PX4 simulation is ready!")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger.info("Terminating PX4 simulation...")

        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(3)
            except subprocess.TimeoutExpired:
                self._logger.warning("Timeout expired")
                self._process.kill()
                self._process.wait()
            self._process.stdout.close()


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    s.bind(('', 0))            # Bind to a free port provided by the host.
    port = s.getsockname()[1]  # Return the port number assigned.
    s.close()
    return port


@contextmanager
def px4_vehicle():
    with PX4Runner(udp_port=find_free_port()) as runner:
        vehicle = dronekit.connect('udpout:127.0.0.1:{}'.format(runner.port))
        yield vehicle
        vehicle.close()
