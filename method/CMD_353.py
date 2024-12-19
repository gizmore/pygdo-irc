from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.IRCUtil import IRCUtil


class CMD_353(IRCCommand):

    async def gdo_execute(self) -> GDT:
        users = self._irc_params[3].split(' ')
        channel = self.init_channel(2)
        gdo_users = []
        for username in users:
            username = IRCUtil.strip_permission(username)
            user = await self._env_server.get_or_create_user(username)
            channel.on_user_joined(user)
            gdo_users.append(user)
        await Application.EVENTS.publish('user_list', channel, gdo_users)
        return self.empty()
