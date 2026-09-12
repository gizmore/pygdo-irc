from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_KICK(IRCCommand):

    async def gdo_execute(self) -> GDT:
        if len(self._irc_params) >= 2:
            channel, target = self._irc_params[:2]
            if target.casefold() == self.irc_connector()._own_nick.casefold():
                reason = self._irc_params[2] if len(self._irc_params) >= 3 else ''
                await Application.EVENTS.publish('irc_bot_kicked', self._env_server, channel, reason)

        return self.empty()
