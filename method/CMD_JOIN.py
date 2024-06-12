from gdo.irc.IRCCommand import IRCCommand


class CMD_JOIN(IRCCommand):

    def gdo_execute(self):
        self._env_user = self.irc_user(self._irc_prefix)
        if self.is_own_user():
            from gdo.irc.method.join import join
            self._env_channel = self._env_server.get_or_create_channel(self._irc_params[0])
            join().env_copy(self).on_bot_joined()
