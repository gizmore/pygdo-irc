from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_PART(IRCCommand):

    def gdo_execute(self):
        self._env_user = self.irc_user(self._irc_prefix)
        channel = self.init_channel()
        channel.on_user_left(self._env_user)
        if self.is_own_user():
            Application.EVENTS.publish('irc_parted', channel, self)
