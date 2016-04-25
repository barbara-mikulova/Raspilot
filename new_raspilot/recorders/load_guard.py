import psutil

from new_raspilot.modules.android_provider import AndroidProvider
from new_raspilot.core.providers.load_guard_controller import BaseLoadGuardStateRecorder
from new_raspilot.raspilot_implementation.commands.system_state_command import SystemStateCommand
from new_raspilot.raspilot_implementation.panic_command import PanicCommand


class RaspilotLoadGuardStateRecorder(BaseLoadGuardStateRecorder):
    STATE_WAS_PANIC = 2
    STATE_WAS_OK = 3

    def __init__(self, panic_limit=85, calm_down_limit=70, panic_delay=100, calm_down_delay=20):
        super().__init__()
        self.__panic_limit = panic_limit
        self.__calm_down_limit = calm_down_limit
        self.__panic_delay = panic_delay
        self.__calm_down_delay = calm_down_delay
        self.__state = RaspilotLoadGuardStateRecorder.STATE_WAS_OK
        self.__android_provider = None

    def initialize(self, raspilot):
        super().initialize(raspilot)
        self.__android_provider = self.raspilot.get_module(AndroidProvider)
        if not self.__android_provider:
            self._log_warning("AndroidProvider NOT found")

    def record_state(self):
        utilization = psutil.cpu_percent()
        if utilization > self.__panic_limit and self.__state is not RaspilotLoadGuardStateRecorder.STATE_WAS_PANIC:
            self.logger.warn('PANIC mode entered, UTILIZATION {}'.format(utilization))
            self.__state = RaspilotLoadGuardStateRecorder.STATE_WAS_PANIC
            self._panic(utilization)
        elif utilization < self.__calm_down_limit and self.__state is not RaspilotLoadGuardStateRecorder.STATE_WAS_OK:
            self.logger.info('CALMED DOWN mode entered, UTILIZATION {}'.format(utilization))
            self.__state = RaspilotLoadGuardStateRecorder.STATE_WAS_OK
            self._calm_down(utilization)

        if self.android_provider:
            command = SystemStateCommand(utilization)
            self.android_provider.send_data(command.serialize())

    def _panic(self, utilization):
        if self.android_provider:
            command = PanicCommand(True, self.__panic_delay, utilization)
            self.android_provider.send_data(command.serialize())
            # TODO: Send message to Arduino

    def _calm_down(self, utilization):
        if self.android_provider:
            command = PanicCommand(False, self.__calm_down_delay, utilization)
            self.android_provider.send_data(command.serialize)
            # TODO: Send message to Arduino

    @property
    def android_provider(self):
        return self.__android_provider