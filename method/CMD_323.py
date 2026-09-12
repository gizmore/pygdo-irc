from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_323(IRCCommand):
    """Forward RPL_LISTEND to optional listeners."""

    async def gdo_execute(self) -> GDT:
        await Application.EVENTS.publish('irc_list_finished', self._env_server)
        return self.empty()
