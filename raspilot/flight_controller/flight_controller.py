import time

from up.flight_controller.base_flight_controller import BaseFlightController

from raspilot.commands.flight_mode_command import FlightModeCommand, \
    FlightModeCommandHandler
import raspilot.modules.arduino_provider


class RaspilotFlightController(BaseFlightController):
    MAX_ROLL_ANGLE = 45
    MAX_PITCH_ANGLE = 45
    MIN_PWM = 1000
    MAX_PWM = 2000
    MIN_ANGLE = 0
    MAX_ANGLE = 180
    STAB_CONSTRAINT = 250
    RATE_CONSTRAINT = 500

    FLIGHT_MODE_RATE = 'Rate'
    FLIGHT_MODE_FBW = 'FBW'
    FLIGHT_MODE_RTH = 'RTH'

    def __init__(self):
        super().__init__()
        self.__arduino_provider = None
        self.__mode_change_handle = None

    def initialize(self, raspil):
        super().initialize(raspil)
        self.__arduino_provider = self.up.get_module(raspilot.modules.arduino_provider.ArduinoProvider)
        if not self.__arduino_provider:
            raise ValueError("Arduino Provider must be loaded")

    def stop(self):
        self.set_flight_mode(self.FLIGHT_MODE_RATE)
        super().stop()
        self.up.command_executor.unregister_command(FlightModeCommand.NAME, self.__mode_change_handle)

    def start(self):
        self.__mode_change_handle = self.up.command_executor.register_command(
            FlightModeCommand.NAME,
            FlightModeCommandHandler(self.up.flight_control)
        )
        return True

    def set_flight_mode(self, mode):
        self.__arduino_provider.set_flight_mode(mode)

    def _notify_loop(self):
        while self._run:
            # TODO
            time.sleep(0.5)
