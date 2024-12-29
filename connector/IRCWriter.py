import time

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Thread import Thread
from gdo.base.Util import Strings
from gdo.irc.connector.IRCSendQueue import IRCSendQueue


class IRCWriter(Thread):
    """
    Thread class for sending messages to the IRC server.
    """
    _connector: 'IRC'
    _queue: IRCSendQueue

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        self._queue = IRCSendQueue(irc_connector)

    def run(self):
        try:
            self.name = f"IRC-Writer({self._connector._server.get_name()})"
            super().run()
            Logger.debug("Starting IRC Send queue")
            while self._connector.is_connected() and Application.RUNNING:
                message = self._queue.get_next_message_to_process()
                if message:
                    self.write_now(message._result)
                    time.sleep(self._queue.get_next_sleep_time())
                else:
                    time.sleep(0.05)
        except Exception as e:
            self._connector.disconnect(str(e))

    def write(self, prefix: str, message: Message):
        Logger.debug(f"IRCWriter.write({prefix}{message._result})")
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        chunk_size = CMD_PRIVMSG().env_copy(message).get_max_msg_len()
        chunks = Strings.split_boundary(message._result, chunk_size - len(prefix) - 16)
        for chunk in chunks:
            msg = Message(message._message, message._env_mode).env_copy(message).result(prefix + chunk)
            if self._queue.get_next_sleep_time() == 0:
                self.write_now(prefix + msg._result)
            else:
                self._queue.append(msg)

    def write_now(self, message: str):
        Logger.debug(f"{self._connector._server.get_name()} >> {message}")
        try:
            message += "\n"
            self._connector._socket.send(message.encode('utf-8'))
        except Exception as ex:
            Logger.exception(ex)
            self._connector.disconnect(str(ex))
