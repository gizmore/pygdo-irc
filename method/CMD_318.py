from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_318(IRCCommand):
    async def gdo_execute(self):
        if not self._irc_prefix or '!' in self._irc_prefix or len(self._irc_params) < 2:
            return self.empty()
        connector = self._env_server.get_connector()
        if self._irc_params[0].casefold() != connector._own_nick.casefold():
            return self.empty()
        nickname = self._irc_params[1]
        user = self._env_server._users.get(nickname)
        if not user:
            return self.empty()
        key = user.get_name_sid()
        pending = autologin.PENDING.get(key)
        if (pending and pending['connector'] is connector
                and pending['reader'] is connector._recv_thread
                and key not in autologin.EUIRC_STATUS):
            autologin().env_server(self._env_server).finish_pending(user, False)
        return self.empty()
