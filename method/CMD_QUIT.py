from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_QUIT(IRCCommand):

    async def gdo_execute(self) -> GDT:
        self._env_user = await self.irc_user(self._irc_prefix)
        await self._env_server.on_user_quit(self._env_user)
        return self.empty()
