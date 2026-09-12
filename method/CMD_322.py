from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_322(IRCCommand):
    """Forward one RPL_LIST entry to optional listeners."""

    async def gdo_execute(self) -> GDT:
        if len(self._irc_params) >= 3:
            name = self._irc_params[1]
            try:
                users = int(self._irc_params[2])
            except ValueError:
                users = 0
            topic = self._irc_params[3] if len(self._irc_params) >= 4 else ''
            await Application.EVENTS.publish('irc_list_entry', self._env_server, name, users, topic)
        return self.empty()
