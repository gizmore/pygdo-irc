from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_NICK(IRCCommand):

    async def gdo_execute(self) -> GDT:
        old_user = await self.irc_user(self._irc_prefix)
        new_user = await self.irc_user(self._irc_params[0])
        old_user._authenticated = False
        channels = self._env_server.get_channels_for_user(old_user)
        self._env_server.on_user_quit(old_user)
        self._env_server.on_user_joined(new_user)
        for channel in channels:
            channel.on_user_joined(new_user)
        return self.empty()
