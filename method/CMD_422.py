from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_422(IRCCommand):
    """RPL_NOMOTD still completes the IRC server welcome."""

    async def gdo_execute(self) -> GDT:
        self._env_server.connection_completed = True
        await Application.EVENTS.publish('irc_connection_completed', self._env_server)
        return self.empty()
