"""SIMULATION ONLY: the hardware teammate can replace this class later.

No Telemetrix import, serial-port connection, or motor calls exist here.
The UI has no dependency on board pins or motor drivers.
"""
from copy import deepcopy
from threading import Lock
from time import monotonic


class RobotInterface:
    def __init__(self):
        self._lock = Lock()
        self._last_received = None
        self._command = {
            'wheel': {'speed': 0, 'direction': 'stop'},
            'arm': {'speed': 0, 'direction': 'stop', 'claw': 'open'},
        }

    def apply_command(self, command):
        """Receive a validated command from Flask and store it for demonstration.

        Hardware integration point: translate speed/direction/claw to the
        team's tested Telemetrix calls, once board, pins and drivers are known.
        This method currently DOES NOT move any motors.
        """
        with self._lock:
            self._command = deepcopy(command)
            self._last_received = monotonic()

    def status(self):
        with self._lock:
            age = None if self._last_received is None else monotonic() - self._last_received
            return {
                'mode': 'simulation',
                'hardware_connected': False,
                'telemetrix_included': False,
                'port': None,
                'last_command': deepcopy(self._command),
                'last_command_age_seconds': age,
            }
