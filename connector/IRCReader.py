from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Render import Mode
from gdo.base.Thread import Thread


class IRCReader(Thread):
    """
    Thread class for receiving messages from the IRC server.
    """
    _connector: 'IRC'

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        # Logger.debug('New IRC reader')

    def run(self):
        # try:
        # Logger.debug("Starting IRC reader")
        self.name = f"IRC-Reader({self._connector._server.get_name()})"
        super().run()
        while self._connector.is_connected() and Application.RUNNING:
            try:
                self._connector.process_message(self.read_irc_line())
            except Exception as ex:
                Logger.exception(ex)

    def read_irc_line(self):
        sock = self._connector._socket
        buffer = b""
        while True:
            data = sock.recv(1)
            if not data:
                break
            buffer += data
            if data == b'\n':
                break
        return buffer.decode().strip()
