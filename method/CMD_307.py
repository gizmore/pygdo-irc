from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_307(IRCCommand):
    async def gdo_execute(self):
        # Server numerics only, and only for an existing euIRC WHOIS probe.
        if self._irc_prefix and '!' not in self._irc_prefix and len(self._irc_params) >= 2:
            await autologin().env_copy(self).euirc_registered_nick(self._irc_params[1])
        return self.empty()
