import json
import logging
import os
import signal
import subprocess

from twisted.internet import reactor
from twisted.internet.endpoints import UNIXServerEndpoint, TCP4ServerEndpoint
from twisted.internet.protocol import Factory, Protocol

from raspilot_implementation.utils.raspilot_logger import RaspilotLoggerFactory

RASPILOT_KILL_TIMEOUT = 5

LOGGER_NAME = 'raspilot_runner'
PORT = 3002


class RaspilotRunner:
    """
    Spawns new Raspilot instance upon receiving request to do so. Only one Raspilot instance can be running at the time.
    When the Raspilot stops, it should notify the RaspilotRunner, which kills the Raspilot instance if does not exit
    within given time.
    """
    def __init__(self):
        self.__logger = logging.getLogger(LOGGER_NAME)
        self.__logger.info("Starting Raspilot Runner")
        my_dir = os.path.dirname(__file__)
        unix_socket_addr = os.path.join(my_dir, "../shared/raspilot_runner.sock")

        raspilot_endpoint = UNIXServerEndpoint(reactor, unix_socket_addr)
        raspilot_endpoint.listen(RaspilotProtocolFactory(RaspilotProtocol(self)))

        spawn_endpoint = TCP4ServerEndpoint(reactor, PORT)
        self.__protocol = RaspilotSpawnProtocol(self)
        spawn_endpoint.listen(RaspilotProtocolFactory(self.__protocol))

        self.__raspilot_process = None

    def on_raspilot_message(self):
        """
        Called after receiving message from Raspilot instance. Waits for the specified time and then kills the Raspilot.
        :return: returns nothing
        """
        try:
            if self.__raspilot_process:
                self.__logger.info('Waiting for Raspilot to exit...')
                self.__raspilot_process.wait(RASPILOT_KILL_TIMEOUT)
        except subprocess.TimeoutExpired:
            self.__logger.error('Killing Raspilot it because did not exit')
            self.__raspilot_process.kill()
        finally:
            self.__raspilot_process = None

    def on_spawn_request(self):
        """
        Called after receiving the spawn request. If no Raspilot instance is running, spawns the Raspilot and notifies
        the requesting client otherwise only send message to the client, nothing is spawned.
        :return: returns nothing
        """
        if not self.__raspilot_process:
            self.__logger.info('Spawning new Raspilot')
            my_dir = os.path.dirname(__file__)
            raspilot_impl_dir = os.path.join(my_dir, '../raspilot_implementation/main.py')
            path_to_script = os.path.abspath(raspilot_impl_dir)
            self.__logger.debug("Running {}".format(path_to_script))
            self.__raspilot_process = subprocess.Popen(['python3', path_to_script], stdout=subprocess.DEVNULL,
                                                       stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            self.__logger.info("Raspilot running with PID {}".format(self.__raspilot_process.pid))
            if self.__protocol.transport:
                message = self.__create_spawn_message('Raspilot ready')
                self.__protocol.transport.write(self.__encode_message(message))
        else:
            if self.__protocol.transport:
                message = self.__create_spawn_message('Raspilot already running')
                self.__protocol.transport.write(self.__encode_message(message))
            self.__logger.warning('Raspilot already running')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called upon exiting the 'with block'. If Raspilot instance was left running, sends SIGINT, and waits for
        Raspilot to exit. If Raspilot does not exit within given time, kills it.
        @param exc_type:
        @param exc_val:
        @param exc_tb:
        @return: returns nothing
        """
        if self.__raspilot_process:
            try:
                self.__logger.info("Asking Raspilot with PID {} to exit".format(self.__raspilot_process.pid))
                os.kill(self.__raspilot_process.pid, signal.SIGINT)
                self.__raspilot_process.wait(5)
                self.__logger.info("Raspilot exited")
            except subprocess.TimeoutExpired:
                self.__logger.error("Raspilot is still running, killing it")
                self.__raspilot_process.kill()

    @staticmethod
    def __encode_message(message):
        """
        Encodes given message as JSON. Returns bytes array representing the JSON when encoded with utf-8.
        :param message: message to be encoded
        :return: bytes array representing the JSON when encoded with utf-8
        :rtype: dict
        """
        json_data = json.dumps(message)
        json_data += '\n'
        return bytes(json_data.encode('utf-8'))

    def __create_spawn_message(self, message, spawned=True, error=None):
        """
        Creates spawn message which is sent to the client.
        :param message: message which should be human readable
        :param spawned: boolean flag, if spawn was successful
        :param error: explanation of error, if an error occurred
        :return: message which is sent to the client
        :rtype: dict
        """
        return {'message': message, 'spawned': spawned, 'error': error,
                'myAddress': self.__protocol.transport.client[0]}


class RaspilotProtocol(Protocol):
    """
    Simple protocol, which calls the callback method on_raspilot_message upon receiving data. Used when checking
    whether the Raspilot exits or not.
    """
    def __init__(self, callbacks):
        self.__callbacks = callbacks

    def dataReceived(self, data):
        self.__callbacks.on_raspilot_message()


class RaspilotSpawnProtocol(Protocol):
    """
    Simple protocol, which calls the callback method on_spawn_request upon receiving data. Used when spawning Raspilot.
    """
    def __init__(self, callbacks):
        self.__callbacks = callbacks

    def dataReceived(self, data):
        self.__callbacks.on_spawn_request()


class RaspilotProtocolFactory(Factory):
    def __init__(self, protocol):
        self.__protocol = protocol

    def buildProtocol(self, addr):
        return self.__protocol


if __name__ == "__main__":
    my_dir = os.path.dirname(__file__)
    logs_path = os.path.join(my_dir, '../logs/')
    RaspilotLoggerFactory.create(LOGGER_NAME, logging.DEBUG, logs_path)
    runner = RaspilotRunner()
    with runner:
        reactor.run()
