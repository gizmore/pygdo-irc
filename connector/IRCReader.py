import asyncio

from gdo.base.Application import Application
from gdo.base.Thread import Thread


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gdo.irc.connector.IRC import IRC


class IRCReader(Thread):
    """
    Thread class for receiving messages from the IRC server.
    """
    _connector: 'IRC'

    def __init__(self, irc_connector):
        super().__init__()
        self._connector = irc_connector
        self.name = self._connector._server.get_name() + " IRCReader"
        self.sock = None
        # Logger.debug('New IRC reader')

    def run(self):
        self.name = f"IRC-Reader({self._connector._server.get_name()})"
        super().run()
        self._connector._socket.setblocking(False)
        asyncio.create_task(self.run_())

    async def run_(self):
        while self._connector.is_connected() and Application.RUNNING:
            if line := await self.read_irc_line():
                await self._connector.process_message(line)
            # await asyncio.sleep(0.05)

    async def read_irc_line(self):
        data = await self.sock.readline()
        return data.decode().strip()
