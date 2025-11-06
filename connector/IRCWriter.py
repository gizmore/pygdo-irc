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
        asyncio.run_coroutine_threadsafe(self.run_(), loop=Application.LOOP)

    async def run_(self):
        try:
            while self._connector.is_connected() and Application.RUNNING:
                message = await self._queue.get_next_message_to_process()
                if message:
                    await self.write_now(message._result)
                    await asyncio.sleep(self._queue.get_next_sleep_time())
                else:
                    await asyncio.sleep(0.05)
        except Exception as e:
            Logger.exception(e)
            self._connector.disconnect(str(e))

    async def write(self, prefix: str, message: Message):
        Logger.debug(f"IRCWriter.write({prefix}{message._result})")
        from gdo.irc.method.CMD_PRIVMSG import CMD_PRIVMSG
        chunk_size = CMD_PRIVMSG().env_copy(message).get_max_msg_len()
        chunks = Strings.split_boundary(message._result, chunk_size - len(prefix) - 16)
        for chunk in chunks:
            msg = Message(message._message, message._env_mode).env_copy(message).result(prefix + chunk)
            if self._queue.get_next_sleep_time() == 0:
                await self.write_now(prefix + msg._result)
            else:
                await self._queue.append(msg)

    async def write_now(self, message: str):
        Logger.debug(f"{self._connector._server.get_name()} >> {message}")
        try:
            message += "\n"
            self.sock.write(message.encode('utf-8'))
            await self.sock.drain()
        except Exception as ex:
            Logger.exception(ex)
            self._connector.disconnect(str(ex))
