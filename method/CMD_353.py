from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.IRCUtil import IRCUtil


class CMD_353(IRCCommand):

    def gdo_execute(self):
        users = self._irc_params[3].split(' ')
        channel = self.init_channel(2)
        for username in users:
            username = IRCUtil.strip_permission(username)
            user = self._env_server.get_or_create_user(username)
            channel.on_user_joined(user)
