import asyncio

from gdo.base.Application import Application
import time
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

    # IRC servers add ``:nick!user@host `` when relaying a client line.  The
    # configured line limit applies to that final wire line on strict servers,
    # not merely to our outgoing ``PRIVMSG`` command.  Keep a conservative
    # reserve so formatting control bytes cannot make the visible tail vanish.
    SERVER_PREFIX_RESERVE = 64

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        self._queue = IRCSendQueue(irc_connector)
        self.name = f"{self._connector._server.get_name()} IRCWriter"
        self.sock = None

    def run(self):
        self.name = f"IRC-Writer({self._connector._server.get_name()})"
        super().run()
        Logger.debug("Starting IRC Send queue")
        asyncio.create_task(self.run_())

    async def run_(self):
        try:
            while self._connector.is_connected() and Application.RUNNING:
                message = await self._queue.get_next_message_to_process()
                if message:
                    await self._queue.wait_for_send_slot()
                    await self.write_now(message._result)
        except Exception as e:
            Logger.exception(e)
            self._connector.disconnected()

    async def write(self, prefix: str, message: Message):
        Logger.debug(f"IRCWriter.write({prefix}{message._result})")
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        line_limit = CMD_PRIVMSG().env_copy(message).get_max_msg_len()
        chunk_size = line_limit - len((prefix + '\r\n').encode('utf-8')) - self.SERVER_PREFIX_RESERVE
        chunks = self.split_utf8_boundary(message._result, chunk_size)
        for chunk in chunks:
            msg = Message(message._message, message._env_mode).env_copy(message).result(prefix + chunk)
            # Only IRC protocol commands use write_now().  User-visible
            # replies always pass through the flood queue, including chunks of
            # one long response.
            await self._queue.append(msg)

    @staticmethod
    def split_utf8_boundary(text: str, byte_limit: int) -> list[str]:
        """Split text without exceeding an IRC line's UTF-8 payload limit."""
        if byte_limit < 1:
            raise ValueError('IRC prefix leaves no room for a message.')
        chunks = []
        while text:
            if len(text.encode('utf-8')) <= byte_limit:
                chunks.append(text)
                break
            length = 0
            end = 0
            for index, char in enumerate(text):
                char_len = len(char.encode('utf-8'))
                if length + char_len > byte_limit:
                    break
                length += char_len
                end = index + 1
            boundary = text.rfind(' ', 0, end)
            if boundary > 0:
                end = boundary
            chunks.append(text[:end])
            text = text[end:]
        return chunks

    async def write_now(self, message: str):
        Logger.debug(f"{self._connector._server.get_name()} >> {message}")
        try:
            message += "\n"
            self.sock.write(message.encode('utf-8'))
            await self.sock.drain()
        except Exception as ex:
            Logger.exception(ex)
            self._connector.disconnect(str(ex))
