from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_PART(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        channel = self.init_channel()
        channel.on_user_left(self._env_user)
        if self.is_own_user():
            await Application.EVENTS.publish('irc_parted', channel, self)
        else:
            await Application.EVENTS.publish('irc_user_parted', channel, self._env_user, self)
        return self.empty()
