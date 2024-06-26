from gdo.base.Application import Application
from gdo.irc.IRCCommand import IRCCommand


class CMD_JOIN(IRCCommand):

    def gdo_execute(self):
        self._env_user = self.irc_user(self._irc_prefix)
        if self.is_own_user():
            channel = self.init_channel()
            Application.EVENTS.publish('irc_joined', channel, self)
            from gdo.irc.method.join import join
            join().env_copy(self).on_bot_joined()
