from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_NICK(IRCCommand):

    async def gdo_execute(self) -> GDT:
        old_user = await self.irc_user(self._irc_prefix)
        nickname = self._irc_params[0]
        connector = self.irc_connector()
        is_own_nick = old_user.get_name().casefold() == connector._own_nick.casefold()
        new_user = await self.irc_user(nickname)
        old_user._authenticated = False
        channels = self._env_server.get_channels_for_user(old_user)
        await self._env_server.on_user_quit(old_user)
        await self._env_server.on_user_joined(new_user)
        for channel in channels:
           await channel.on_user_joined(new_user)
        if is_own_nick:
            await connector.nick_changed(nickname)
            await connector.setup_dog_user(nickname)
        return self.empty()
