from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_NOTICE(IRCCommand):

    async def gdo_execute(self) -> GDT:
        # Application.EVENTS.publish(f'irc{self._env_server.get_id()}_notice', self)
        pass
