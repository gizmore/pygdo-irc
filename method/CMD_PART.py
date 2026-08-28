from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_PART(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        self._env_server = self._env_user.get_server()
        for name in self._irc_params[0].split(','):
            self._env_channel = self.irc_channel(name)
            if self.is_own_user():
                await self._env_channel.on_bot_left(self._env_user)
            else:
                await self._env_channel.on_user_left(self._env_user)
        return self.empty()
