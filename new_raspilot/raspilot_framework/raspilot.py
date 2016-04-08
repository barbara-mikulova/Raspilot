from threading import Event

from twisted.internet import reactor

from new_raspilot.raspilot_framework.commands.command_executor import CommandExecutor
from new_raspilot.raspilot_framework.commands.command_receiver import CommandReceiver
from new_raspilot.raspilot_framework.utils.raspilot_logger import RaspilotLogger


class Raspilot:
    def __init__(self, builder):
        """
        :param builder: RaspilotBuilder used to configure this instance
        :type builder: RaspilotBuilder
        """
        self.__logger = RaspilotLogger.get_logger()
        self.__providers = []
        self.__stop_event = Event()
        self.__command_executor = builder.command_executor
        self.__command_receiver = builder.command_receiver
        self.__orientation_provider = builder.orientation_provider
        for provider in builder.custom_providers:
            self.__providers.append(provider)

    def initialize(self):
        self.__command_executor.initialize(self)
        self.__command_receiver.initialize(self)
        self.__orientation_provider.initialize(self)
        for provider in self.__providers:
            provider.initialize(self)

    def run(self):
        self.__orientation_provider.start()
        for provider in self.__providers:
            provider.start()
        self.__logger.debug("Running Twisted reactor")
        reactor.run()

    def stop(self):
        self.__stop_event.set()
        self.__orientation_provider.stop()
        for provider in self.__providers:
            provider.stop()

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def command_receiver(self):
        return self.__command_receiver

    @property
    def command_executor(self):
        return self.__command_executor

    @property
    def orientation_provider(self):
        return self.__orientation_provider


class RaspilotBuilder:
    def __init__(self):
        self.__custom_providers = []
        self.__command_receiver = CommandReceiver()
        self.__command_executor = CommandExecutor()
        self.__orientation_provider = None

    def add_custom_provider(self, provider):
        self.__custom_providers.append(provider)
        return self

    def with_command(self, name, handler):
        self.__command_executor.register_command(name, handler)

    def with_orientation_provider(self, provider):
        self.__orientation_provider = provider

    def build(self):
        """
        Build Raspilot instance with specified configuration
        :rtype Raspilot
        """
        self.__validate()
        return Raspilot(self)

    def __validate(self):
        if not self.orientation_provider:
            raise ValueError("Orientation Provider must be set")

    @property
    def custom_providers(self) -> list:
        return self.__custom_providers

    @property
    def command_receiver(self) -> CommandReceiver:
        return self.__command_receiver

    @property
    def command_executor(self) -> CommandExecutor:
        return self.__command_executor

    @property
    def orientation_provider(self):
        return self.__orientation_provider