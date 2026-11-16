from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_307(IRCCommand):
    async def gdo_execute(self):
        if self._irc_prefix and '!' not in self._irc_prefix and len(self._irc_params) >= 2:
            helper = autologin().env_copy(self)
            network = self._env_server.get_name().casefold()
            if network in ('germanleets', 'rizon'):
                expected = ('is identified for this nick' if network == 'germanleets'
                            else 'has identified for this nick')
                if (len(self._irc_params) == 3 and
                        self._irc_params[0].casefold() == self._env_server.get_connector()._own_nick.casefold() and
                        self._irc_params[2].strip().casefold() == expected):
                    await helper.identified_nick(self._irc_params[1])
            else:
                await helper.euirc_registered_nick(self._irc_params[1])
        return self.empty()
