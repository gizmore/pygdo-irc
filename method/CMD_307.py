from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_307(IRCCommand):
    async def gdo_execute(self):
        if self._irc_prefix and '!' not in self._irc_prefix and len(self._irc_params) >= 2:
            helper = autologin().env_copy(self)
            if self._env_server.get_name().casefold() == 'germanleets':
                if (len(self._irc_params) == 3 and
                        self._irc_params[0].casefold() == self._env_server.get_connector()._own_nick.casefold() and
                        self._irc_params[2].strip().casefold() == 'is identified for this nick'):
                    await helper.identified_nick(self._irc_params[1])
            else:
                await helper.euirc_registered_nick(self._irc_params[1])
        return self.empty()
