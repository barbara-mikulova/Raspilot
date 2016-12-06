from up.base_started_module import BaseStartedModule

from raspilot.commands.pid_tunings_command import PIDTuningsCommand, \
    PIDTuningsCommandHandler, PIDSyncCommandHandler, PIDSyncCommand


class PIDTuningsProvider(BaseStartedModule):
    def _execute_start(self):
        self.raspilot.command_executor.register_command(PIDTuningsCommand.NAME, PIDTuningsCommandHandler())
        self.raspilot.command_executor.register_command(PIDSyncCommand.NAME, PIDSyncCommandHandler())
        return True

    def load(self):
        return True