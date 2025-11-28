from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_JOIN(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = self.irc_user(self._irc_prefix)
        channel = self.init_channel()
        await channel.on_user_joined(self._env_user)
        if self.is_own_user():
            await Application.EVENTS.publish('irc_joined', channel, self._env_user, self)
            from gdo.irc.method.join import join
            join().env_copy(self).on_bot_joined()
        return self.empty()
