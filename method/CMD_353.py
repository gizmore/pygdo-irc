from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.IRCUtil import IRCUtil


class CMD_353(IRCCommand):

    async def gdo_execute(self) -> GDT:
        users = self._irc_params[3].split(' ')
        channel = self.init_channel(2)
        for username in users:
            username = IRCUtil.strip_permission(username)
            user = await self._env_server.get_or_create_user(username)
            # NAMES is the initial presence snapshot after connecting.  It
            # must enter the same server lifecycle as a later JOIN, otherwise
            # modules such as Fun never receive a join timestamp for users
            # who were already present when we connected.
            await self._env_server.on_user_joined(user, channel)
            await channel.on_user_joined(user)
