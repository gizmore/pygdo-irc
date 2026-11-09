from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand
from gdo.irc.method.autologin import autologin


class CMD_330(IRCCommand):

    async def gdo_execute(self) -> GDT:
        if not self._irc_prefix or '!' in self._irc_prefix or len(self._irc_params) < 2:
            return self.empty()
        user = await self._env_server.get_or_create_user(self._irc_params[1])
        await autologin().env_copy(self).confirm_probe(user)
        return self.empty()
