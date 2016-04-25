import logging

from obsolete.raspilot.commands import BaseCommandHandler


class ExitCommandHandler(BaseCommandHandler):

    def __init__(self, name):
        super().__init__(name)
        self.__logger = logging.getLogger('raspilot.log')

    def _run_action(self, data, command_id, request, response, raspilot):
        self.__logger.debug("Exiting Raspilot")
        raspilot.stop()