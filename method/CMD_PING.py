from gdo.base.GDT import GDT
from gdo.irc.IRCCommand import IRCCommand


class CMD_PING(IRCCommand):

    async def gdo_execute(self) -> GDT:
        pong = self._irc_params[0]
        await self.irc_connector().send_raw(f"PONG {pong}")
        return self.empty()
