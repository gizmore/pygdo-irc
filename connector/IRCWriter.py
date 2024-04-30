import threading
import time

from gdo.irc.connector.IRCSendQueue import IRCSendQueue


class IRCWriter(threading.Thread):
    """
    Thread class for receiving messages from the IRC server.
    """
    _connector: 'IRC'
    _queue: IRCSendQueue

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        self._queue = IRCSendQueue(irc_connector)

    def run(self):
        try:
            while self._connector.is_connected():
                method = self._queue.get_next_method_to_process()
                time.sleep(self._queue.get_next_method_sleep_time())
                method.reply()
                self._connector.process_message(data.decode('utf-8'))
        except Exception as e:
            self._connector.disconnect(str(e))
