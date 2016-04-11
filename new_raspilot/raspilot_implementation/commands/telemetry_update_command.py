import uuid

from new_raspilot.raspilot_framework.commands.command import Command


class TelemetryUpdateCommand(Command):
    NAME = 'telemetry.update'

    def __init__(self, data):
        super().__init__()
        self.name = TelemetryUpdateCommand.NAME
        self.data = data
        self.id = str(uuid.uuid1())

    @classmethod
    def create_from_system_state(cls, system_state):
        data = {'orientation': system_state.get('orientation', None)}
        c = TelemetryUpdateCommand(data)
        return c