import threading

from gdo.base.Logger import Logger


class IRCReader(threading.Thread):
    """
    Thread class for receiving messages from the IRC server.
    """
    _connector: 'IRC'

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        Logger.debug('New IRC reader')

    def run(self):
        try:
            Logger.debug("Starting IRC reader")
            while self._connector.is_connected():
                Logger.debug("reading")
                data = self._connector._sock.recv(1024)
                self._connector.process_message(data.decode('utf-8'))
        except Exception as e:
            self._connector.disconnect(str(e))
