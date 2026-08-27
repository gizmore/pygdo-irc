from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_NOTICE(IRCCommand):

    async def gdo_execute(self) -> GDT:
        sender = (self._irc_prefix or '').split('!', 1)[0]
        if sender.casefold() == 'nickserv' and len(self._irc_params) > 1:
            from gdo.irc.method.signup import signup
            await signup().env_copy(self).on_nickserv_notice(self._irc_params[1])
        return self.empty()
