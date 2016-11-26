import json
import json.decoder

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory, connectionDone
from twisted.protocols.basic import LineReceiver

from new_raspilot.core.base_started_module import BaseStartedModule
from new_raspilot.core.commands.command import BaseCommand
from new_raspilot.core.utils.raspilot_logger import RaspilotLogger
from new_raspilot.raspilot_implementation.commands.altitude_change_command import AltitudeChangeCommand


class AndroidProvider(BaseStartedModule):
    def __init__(self):
        super().__init__()

    def _execute_initialization(self):
        self.__protocol = AndroidProtocol(self.raspilot.command_receiver)

    def _execute_start(self):
        endpoint = TCP4ServerEndpoint(reactor, 50001)
        endpoint.listen(AndroidProtocolFactory(self.__protocol))
        return True

    def _execute_stop(self):
        pass

    def send_data(self, data):
        if self.__protocol.transport:
            reactor.callFromThread(self.__protocol.sendLine, data)
        else:
            self.__protocol.enqueue(data)

    def load(self):
        return True


class AndroidProtocol(LineReceiver):
    def __init__(self, callbacks):
        super().__init__()
        self.delimiter = bytes([10])
        self.__logger = RaspilotLogger.get_logger()
        self.__callbacks = callbacks
        self.__queue = []

    def enqueue(self, data):
        self.__queue.append(data)

    def rawDataReceived(self, data):
        self.__logger.debug("Raw data received {}".format(data))

    def lineReceived(self, line):
        """
        Parses the received line into a JSON object. Then creates a Command from this data and notifies callbacks about
        receiving the command. json.JSONDecodeError is logged if risen as well as general Exception which might occur
        during callbacks invocation.
        :param line: received line
        :return: None
        """
        if not bytes(AltitudeChangeCommand.NAME, 'utf-8') in line:
            self.__logger.debug("Data received {}".format(line))
        try:
            parsed_data = json.loads(line.decode('utf-8'))
            self.__callbacks.execute_command(BaseCommand.from_json(parsed_data))
        except json.decoder.JSONDecodeError as e:
            self.__logger.error("Invalid data received.\n\tData were {}.\n\tException risen is {}".format(line, e))
        except Exception as e:
            self.__logger.critical(
                "Exception occurred during data processing.\n\tData were {}.\n\tException risen is {}".format(line, e))

    def connectionMade(self):
        """
        If enqueued data for the Android exists, sends the data and clears the queue
        :return: None
        """
        self.__logger.info("Connection from {} opened".format(self.transport.client[0]))
        for data in self.__queue:
            self.sendLine(data)
        self.__queue.clear()

    def connectionLost(self, reason=connectionDone):
        self.__logger.info("Connection lost")


class AndroidProtocolFactory(Factory):

    def __init__(self, protocol):
        super().__init__()
        self.__protocol = protocol

    def buildProtocol(self, addr):
        return self.__protocol
