from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_JOIN(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_server = self._env_user.get_server()
        for name in self._irc_params[0].split(','):
            self._env_channel = self.irc_channel(name)
            if self.is_own_user():
                await self._env_server.on_bot_joined(self._env_user, self._env_channel)
                await self._env_channel.on_bot_joined(self._env_user)
                from gdo.irc.method.join import join
                join().env_copy(self).on_bot_joined()
            else:
                await self._env_server.on_user_joined(self._env_user, self._env_channel)
                await self._env_channel.on_user_joined(self._env_user)
        return self.empty()
