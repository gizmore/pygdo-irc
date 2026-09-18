from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_432(IRCCommand):
    """Pick a safe fallback nick when the server reserves the configured one."""

    async def gdo_execute(self) -> GDT:
        await self._env_server.get_connector().send_nick_cmd()
        return self.empty()
